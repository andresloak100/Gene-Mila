#!/usr/bin/env python3
"""The ledger proxy: the only process in a block H session that holds the DeepSeek key, and the one that counts spend.

    DEEPSEEK_API_KEY="$API_KEY" python tools/baselines/ledger_proxy.py --listen 127.0.0.1:8787 \\
        --upstream https://api.deepseek.com --ledger <MAIN>/runs/spend_ledger.sqlite --run-id h_biomni_r0 \\
        --arm biomni --session-cap-usd 2.50 --block-cap-usd <cap> --log <dir>/proxy.jsonl [--pricing configs/default.toml]

Foreign agents (Biomni, Claude Code) run in an isolated place with a dummy token and a network route to this proxy only
(docs/FEATURE_COMPARISON_PROTOCOL.md, fairness control 7). The proxy:

- forwards POST /v1/chat/completions (OpenAI format, Biomni) and POST /anthropic/v1/messages (Anthropic format, plain
  JSON or SSE streaming, Claude Code with ANTHROPIC_BASE_URL=http://127.0.0.1:8787/anthropic) to the upstream, with
  the client's Authorization and x-api-key headers dropped and `Authorization: Bearer <DEEPSEEK_API_KEY>` from its own
  environment added. Only loopback clients are accepted; any token they send is ignored. POST
  /anthropic/v1/messages/count_tokens is forwarded unpriced (it has no usage). Everything else is 404.
- prices every response from its usage object with the lab's table (`configs/default.toml` [pricing], peak rates, the
  ledger convention) and the lab's formula (genemila/llm.py LLMGateway.cost: cache hits at input_cache_hit, the other
  prompt tokens at input_cache_miss, output at output; Anthropic cache_creation tokens count as misses, as
  genemila/providers/anthropic_api.py counts them), by the served model when the table has it, else the requested one,
  else the pessimistic default entry. OpenAI usage: prompt_tokens, completion_tokens, prompt_cache_hit_tokens
  (prompt_cache_miss_tokens is checked when present); Anthropic: input_tokens, output_tokens,
  cache_read_input_tokens, cache_creation_input_tokens; for SSE the message_start event carries the input side and
  message_delta the output side. A usage object without the required keys is not priced: the client gets 502, the
  log line names the keys seen, and the proxy refuses every later request (it can no longer bound the spend). DeepSeek
  has billed the unpriced call, so the operator adds it to the ledger by hand from the console reading.
- writes one row per priced call to the shared ledger with the lab's own writer (genemila.llm.SpendLedger: provider
  "deepseek", the model, input/output/cached tokens, cost_usd, this run id, role "baseline:<arm>"), so every cap the
  lab reads counts it, and one line per request to the jsonl log: timestamp, route, model requested and served, tokens,
  cost, cumulative session cost, ledger total, status, latency. Never a request or response body (they carry data)
  and never an Authorization value.
- refuses with HTTP 402 and a JSON body when the session has spent its cap, or when the ledger total plus what this
  session may still spend (session cap minus session spend) would exceed the block cap, or when the ledger total alone
  reaches it. The ledger is read at startup and again after every call, so another run writing to it is seen. The
  check is on settled spend: one call can overshoot the session cap by at most its own cost.
- GET /healthz answers {"ok": true, ...} with the caps and the spend, so a runner can check the proxy before starting.

Caveats. The proxy is HTTP/1.0 with Connection: close; the Anthropic and OpenAI SDKs handle that. It verifies the
upstream TLS certificate with the system store. It is a stdlib ThreadingHTTPServer, enough for one agent at a time.
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import socket
import ssl
import sys
import threading
import time
import tomllib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from genemila.llm import SpendLedger  # noqa: E402
from genemila.providers.base import Usage  # noqa: E402

PROVIDER = "deepseek"
KEY_ENV = "DEEPSEEK_API_KEY"
ROUTES = {"/v1/chat/completions": "openai", "/anthropic/v1/messages": "anthropic",
          "/anthropic/v1/messages/count_tokens": "free"}
DROP_HEADERS = {"host", "connection", "content-length", "transfer-encoding", "authorization", "x-api-key",
                "proxy-authorization", "keep-alive", "te", "upgrade"}


class UnknownUsage(ValueError):
    """The upstream's usage object does not have the keys this proxy prices."""


def load_pricing(path: Path) -> dict:
    return tomllib.loads(path.read_text()).get("pricing", {})


def price_key(pricing: dict, requested: str | None, served: str | None) -> str:
    if served and served in pricing:
        return served
    if requested and requested in pricing:
        return requested
    return "default"


def cost_of(pricing: dict, key: str, usage: Usage) -> float:
    p = pricing.get(key) or pricing.get("default") or {"input_cache_hit": 3.0, "input_cache_miss": 3.0, "output": 15.0}
    miss = max(0, usage.input_tokens - usage.cached_tokens)
    return (usage.cached_tokens * p["input_cache_hit"] + miss * p["input_cache_miss"]
            + usage.output_tokens * p["output"]) / 1e6


def _int(d: dict, key: str) -> int:
    v = d.get(key)
    if v is None:
        raise UnknownUsage(key)
    return int(v)


def usage_openai(u: dict) -> Usage:
    """DeepSeek's chat completion usage: prompt_tokens (hits included), completion_tokens, prompt_cache_hit_tokens."""
    if not isinstance(u, dict):
        raise UnknownUsage("usage is not an object")
    prompt, completion = _int(u, "prompt_tokens"), _int(u, "completion_tokens")
    cached = int(u.get("prompt_cache_hit_tokens") or 0)
    if "prompt_cache_miss_tokens" in u and cached + int(u["prompt_cache_miss_tokens"] or 0) != prompt:
        raise UnknownUsage("prompt_cache_hit_tokens + prompt_cache_miss_tokens != prompt_tokens")
    return Usage(input_tokens=prompt, output_tokens=completion, cached_tokens=cached)


def usage_anthropic(u_in: dict, u_out: dict | None = None) -> Usage:
    """Anthropic usage, where input_tokens excludes the cache read and creation counts (the lab's convention:
    input_tokens = all prompt tokens, cached_tokens = reads, creation priced as a miss). u_out is the message_delta
    usage of a stream, which carries output_tokens."""
    if not isinstance(u_in, dict):
        raise UnknownUsage("usage is not an object")
    cached = int(u_in.get("cache_read_input_tokens") or 0)
    created = int(u_in.get("cache_creation_input_tokens") or 0)
    out = u_out if u_out is not None else u_in
    if not isinstance(out, dict):
        raise UnknownUsage("message_delta usage is not an object")
    return Usage(input_tokens=_int(u_in, "input_tokens") + cached + created, output_tokens=_int(out, "output_tokens"),
                 cached_tokens=cached)


class Proxy:
    """The shared state of one proxy process: key, pricing, caps, ledger, log."""

    def __init__(self, upstream: str, ledger: Path, run_id: str, arm: str, session_cap: float, block_cap: float,
                 log: Path, pricing: dict, key: str):
        u = urlsplit(upstream)
        if u.scheme not in ("http", "https") or not u.hostname:
            raise SystemExit(f"refusing: --upstream must be http(s)://host[:port], got {upstream!r}")
        self.scheme, self.host, self.port = u.scheme, u.hostname, u.port or (443 if u.scheme == "https" else 80)
        self.base_path = u.path.rstrip("/")
        self.key, self.pricing = key, pricing
        self.run_id, self.role = run_id, f"baseline:{arm}"
        self.session_cap, self.block_cap = float(session_cap), float(block_cap)
        self.ledger = SpendLedger(ledger)
        self.log_path = Path(log)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.session_spent = 0.0
        self.calls = 0
        self.halted: str | None = None
        self.ledger_total = self.ledger.total(PROVIDER)
        self.ssl_ctx = ssl.create_default_context() if self.scheme == "https" else None

    # ----------------------------------------------------------------- caps
    def refusal(self) -> str | None:
        """Why the next call may not go out, or None. Reads settled spend only; the ledger is re-read here so a
        write by another run since the last call is seen."""
        total = self.ledger.total(PROVIDER)
        with self.lock:
            self.ledger_total = total
            if self.halted:
                return self.halted
            if self.session_spent >= self.session_cap:
                return f"session cap reached: ${self.session_spent:.4f} of ${self.session_cap:.2f}"
            remaining = self.session_cap - self.session_spent
            if self.ledger_total >= self.block_cap:
                return f"block cap reached: ledger ${self.ledger_total:.4f} of ${self.block_cap:.2f}"
            if self.ledger_total + remaining > self.block_cap:
                return (f"block cap: ledger ${self.ledger_total:.4f} plus this session's remaining ${remaining:.4f} "
                        f"would exceed ${self.block_cap:.2f}")
        return None

    def settle(self, model: str, usage: Usage, cost: float) -> None:
        self.ledger.add(self.run_id, PROVIDER, model, self.role, usage, cost)
        with self.lock:
            self.session_spent += cost
            self.calls += 1
            self.ledger_total = self.ledger.total(PROVIDER)

    def halt(self, reason: str) -> None:
        with self.lock:
            self.halted = reason

    # ------------------------------------------------------------------ log
    def log(self, **fields) -> None:
        with self.lock:
            fields.update(ts=time.time(), run_id=self.run_id, session_cost_usd=round(self.session_spent, 6),
                          ledger_total_usd=round(self.ledger_total, 6))
            line = json.dumps(fields, sort_keys=True).replace(self.key, "<redacted>")  # belt and braces
        with self.lock, self.log_path.open("a") as fh:
            fh.write(line + "\n")

    def health(self) -> dict:
        with self.lock:
            return {"ok": self.halted is None, "run_id": self.run_id, "role": self.role, "calls": self.calls,
                    "session_cost_usd": round(self.session_spent, 6), "session_cap_usd": self.session_cap,
                    "ledger_total_usd": round(self.ledger_total, 6), "block_cap_usd": self.block_cap,
                    "halted": self.halted, "upstream": f"{self.scheme}://{self.host}:{self.port}{self.base_path}"}

    # ------------------------------------------------------------- upstream
    def connect(self) -> http.client.HTTPConnection:
        if self.scheme == "https":
            return http.client.HTTPSConnection(self.host, self.port, timeout=600, context=self.ssl_ctx)
        return http.client.HTTPConnection(self.host, self.port, timeout=600)


class Handler(BaseHTTPRequestHandler):
    proxy: Proxy  # set on the server class
    server_version = "gm-ledger-proxy/1"
    sys_version = ""

    def log_message(self, fmt, *args):  # the jsonl log is the record; stderr gets nothing with bodies or tokens
        pass

    # ------------------------------------------------------------- replies
    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, kind: str, message: str) -> None:
        # one body both SDKs parse: OpenAI reads error.message, Anthropic error.type/error.message
        self._json(status, {"type": "error", "error": {"type": kind, "message": message, "code": kind}})

    def _loopback(self) -> bool:
        try:
            return self.client_address[0] in ("127.0.0.1", "::1", "::ffff:127.0.0.1")
        except (IndexError, TypeError):
            return False

    def do_GET(self):
        if not self._loopback():
            return self._error(403, "forbidden", "loopback clients only")
        if self.path.split("?")[0] == "/healthz":
            return self._json(200, self.proxy.health())
        self._error(404, "not_found", "no such route")

    def do_POST(self):
        p = self.proxy
        if not self._loopback():
            return self._error(403, "forbidden", "loopback clients only")
        path = self.path.split("?")[0]
        kind = ROUTES.get(path)
        if kind is None:
            p.log(route=path, status=404, refused="no such route")
            return self._error(404, "not_found", f"this proxy forwards only {sorted(ROUTES)}")
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        requested, stream = None, False
        try:
            req = json.loads(body) if body else {}
            requested, stream = req.get("model"), bool(req.get("stream"))
            if kind == "openai" and stream:  # DeepSeek sends the usage of a stream only when asked
                opts = dict(req.get("stream_options") or {})
                opts["include_usage"] = True
                req["stream_options"] = opts
                body = json.dumps(req).encode()
        except (ValueError, AttributeError):
            pass
        if kind != "free":
            why = p.refusal()
            if why:
                p.log(route=path, model_requested=requested, status=402, refused=why)
                return self._error(402, "budget_cap", f"ledger proxy refuses: {why}")
        t0 = time.monotonic()
        try:
            self._forward(path, kind, body, requested, stream, t0)
        except (OSError, http.client.HTTPException, socket.timeout) as exc:
            p.log(route=path, model_requested=requested, status=502, error=type(exc).__name__)
            try:
                self._error(502, "upstream_error", f"upstream connection failed: {type(exc).__name__}")
            except OSError:
                pass

    # ------------------------------------------------------------ forward
    def _forward(self, path: str, kind: str, body: bytes, requested, stream: bool, t0: float) -> None:
        p = self.proxy
        headers = {k: v for k, v in self.headers.items() if k.lower() not in DROP_HEADERS}
        headers["Authorization"] = f"Bearer {p.key}"
        if kind != "openai":
            headers["x-api-key"] = p.key  # the Anthropic SDK's own header; same key
        headers["Content-Length"] = str(len(body))
        headers["Connection"] = "close"
        conn = p.connect()
        try:
            conn.request("POST", p.base_path + path, body=body, headers=headers)
            resp = conn.getresponse()
            ctype = resp.getheader("Content-Type", "") or ""
            if "text/event-stream" in ctype:
                return self._stream(path, kind, resp, requested, t0)
            data = resp.read()
            latency = round(time.monotonic() - t0, 3)
            if resp.status != 200 or kind == "free":
                p.log(route=path, model_requested=requested, status=resp.status, latency_s=latency, stream=False,
                      priced=False)
                return self._relay(resp.status, ctype, data)
            try:
                doc = json.loads(data)
                served = doc.get("model")
                usage = usage_openai(doc.get("usage")) if kind == "openai" else usage_anthropic(doc.get("usage"))
            except (ValueError, UnknownUsage, AttributeError) as exc:
                return self._unpriced(path, requested, exc, data, latency)
            self._settle(path, requested, served, usage, latency, stream=False)
            self._relay(200, ctype, data)
        finally:
            conn.close()

    def _relay(self, status: int, ctype: str, data: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype or "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def _unpriced(self, path, requested, exc, data: bytes, latency: float) -> None:
        keys: list = []
        try:
            u = json.loads(data).get("usage")
            keys = sorted(u) if isinstance(u, dict) else [f"usage is {type(u).__name__}"]
        except (ValueError, AttributeError):
            keys = ["response is not a JSON object"]
        reason = f"unknown usage shape ({exc}); keys seen: {keys}"
        self.proxy.halt(f"halted after an unpriced response: {reason}")
        self.proxy.log(route=path, model_requested=requested, status=502, latency_s=latency, unpriced=True,
                       usage_keys=keys, error=str(exc)[:200])
        self._error(502, "unpriced_usage", "ledger proxy could not price the upstream usage; the proxy is halted")

    def _settle(self, path, requested, served, usage: Usage, latency: float, stream: bool) -> None:
        p = self.proxy
        key = price_key(p.pricing, requested, served)
        cost = cost_of(p.pricing, key, usage)
        p.settle(served or requested or key, usage, cost)
        p.log(route=path, model_requested=requested, model_served=served, priced_as=key, status=200, stream=stream,
              input_tokens=usage.input_tokens, cached_tokens=usage.cached_tokens, output_tokens=usage.output_tokens,
              cost_usd=round(cost, 8), latency_s=latency)

    def _stream(self, path: str, kind: str, resp, requested, t0: float) -> None:
        """Relay an SSE body line by line while reading its usage events; price at the end."""
        self.send_response(resp.status)
        self.send_header("Content-Type", resp.getheader("Content-Type"))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        served, u_in, u_out, usage_oa, raw_keys = None, None, None, None, []
        event, data_lines = None, []
        while True:
            line = resp.readline()
            if not line:
                break
            self.wfile.write(line)
            self.wfile.flush()
            s = line.decode("utf-8", errors="replace").rstrip("\r\n")
            if s.startswith("event:"):
                event = s[6:].strip()
            elif s.startswith("data:"):
                data_lines.append(s[5:].strip())
            elif s == "":
                payload = "\n".join(data_lines)
                event, data_lines = None, []
                if not payload or payload == "[DONE]":
                    continue
                try:
                    doc = json.loads(payload)
                except ValueError:
                    continue
                if not isinstance(doc, dict):
                    continue
                if kind == "openai":
                    served = doc.get("model") or served
                    if isinstance(doc.get("usage"), dict):
                        usage_oa = doc["usage"]
                else:
                    typ = doc.get("type")
                    if typ == "message_start" and isinstance(doc.get("message"), dict):
                        served = doc["message"].get("model") or served
                        u_in = doc["message"].get("usage")
                    elif typ == "message_delta":
                        u_out = doc.get("usage")
                    if isinstance(doc.get("usage"), dict):
                        raw_keys = sorted(set(raw_keys) | set(doc["usage"]))
        latency = round(time.monotonic() - t0, 3)
        if u_in is None and isinstance(u_out, dict) and "input_tokens" in u_out:
            u_in = u_out  # a server that reports the whole usage in message_delta only
        try:
            usage = usage_openai(usage_oa) if kind == "openai" else usage_anthropic(u_in, u_out)
        except (UnknownUsage, AttributeError) as exc:
            keys = sorted(usage_oa) if isinstance(usage_oa, dict) else raw_keys
            self.proxy.halt(f"halted after an unpriced stream: {exc}; keys seen: {keys}")
            self.proxy.log(route=path, model_requested=requested, model_served=served, status=502, stream=True,
                           latency_s=latency, unpriced=True, usage_keys=keys, error=str(exc)[:200])
            return  # the stream has already been relayed; the next request gets the 402-style halt
        self._settle(path, requested, served, usage, latency, stream=True)


def make_server(listen: str, proxy: Proxy) -> ThreadingHTTPServer:
    host, _, port = listen.rpartition(":")
    cls = type("BoundHandler", (Handler,), {"proxy": proxy})
    srv = ThreadingHTTPServer((host or "127.0.0.1", int(port)), cls)
    srv.daemon_threads = True
    return srv


def build(args: argparse.Namespace) -> Proxy:
    key = os.environ.get(KEY_ENV, "")
    if not key:
        raise SystemExit(f"refusing: {KEY_ENV} is not set in the proxy's environment")
    if args.session_cap_usd <= 0 or args.block_cap_usd <= 0:
        raise SystemExit("refusing: both caps must be positive")
    return Proxy(args.upstream, Path(args.ledger), args.run_id, args.arm or args.run_id, args.session_cap_usd,
                 args.block_cap_usd, Path(args.log), load_pricing(Path(args.pricing)), key)


def parse(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--listen", default="127.0.0.1:8787")
    ap.add_argument("--upstream", default="https://api.deepseek.com")
    ap.add_argument("--ledger", required=True, help="the shared spend ledger (sqlite)")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--arm", default=None, help="the arm name for the ledger role baseline:<arm> (default: the run id)")
    ap.add_argument("--session-cap-usd", type=float, required=True)
    ap.add_argument("--block-cap-usd", type=float, required=True)
    ap.add_argument("--log", required=True, help="the jsonl log (one line per request; never a body or a token)")
    ap.add_argument("--pricing", default=str(REPO_ROOT / "configs" / "default.toml"))
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse(argv)
    if not args.listen.startswith(("127.0.0.1:", "localhost:", "[::1]:")):
        print("refusing: --listen must be a loopback address", file=sys.stderr)
        return 2
    proxy = build(args)
    srv = make_server(args.listen, proxy)
    proxy.log(route="start", status=0, upstream=proxy.health()["upstream"], session_cap_usd=proxy.session_cap,
              block_cap_usd=proxy.block_cap, role=proxy.role)
    why = proxy.refusal()
    print(f"ledger proxy on http://{args.listen} -> {proxy.health()['upstream']}; ledger ${proxy.ledger_total:.4f}, "
          f"session cap ${proxy.session_cap:.2f}, block cap ${proxy.block_cap:.2f}; role {proxy.role}"
          + (f"\nWARNING: every request will be refused: {why}" if why else ""), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
        proxy.log(route="stop", status=0, calls=proxy.calls)
    return 0


if __name__ == "__main__":
    sys.exit(main())
