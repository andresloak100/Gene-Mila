#!/usr/bin/env python3
"""Local pass-through proxy in front of api.deepseek.com for block U (CellForge on our data).

Every CellForge and Codex call goes through it. It forwards the request unchanged (streaming included),
reads the `usage` block of each reply, prices it with the lab's table (configs/default.toml, peak rates)
and appends one line per call to a JSONL ledger. Once the running total reaches the cap it answers
HTTP 402 and forwards nothing more. It never logs headers or bodies, so the key never touches disk.

    python deepseek_proxy.py --port 8787 --ledger ledger.jsonl --cap-usd 15 [--upstream https://api.deepseek.com]
"""
import argparse, json, sys, threading, time, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PRICE = {  # USD per million tokens, peak rates, same as configs/default.toml [pricing.*]
    "deepseek-v4-pro": {"hit": 0.044, "miss": 1.32, "out": 3.96},
    "deepseek-flash": {"hit": 0.006, "miss": 0.30, "out": 1.20},
    "deepseek-chat": {"hit": 0.006, "miss": 0.30, "out": 1.20},
    "default": {"hit": 3.0, "miss": 3.0, "out": 15.0},
}
LOCK = threading.Lock()
STATE = {"total_usd": 0.0, "calls": 0, "refused": 0}


def price(model, usage):
    p = PRICE.get(model, PRICE["default"])
    pt = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
    hit = usage.get("prompt_cache_hit_tokens") or (usage.get("input_tokens_details") or {}).get("cached_tokens") or 0
    out = usage.get("completion_tokens") or usage.get("output_tokens") or 0
    return (hit * p["hit"] + (pt - hit) * p["miss"] + out * p["out"]) / 1e6, pt, hit, out


def record(path, model, usage, stream, status, seconds, upstream_path):
    usd, pt, hit, out = price(model, usage or {})
    with LOCK:
        STATE["total_usd"] += usd
        STATE["calls"] += 1
        row = {"t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "path": upstream_path, "model": model,
               "stream": stream, "status": status, "prompt_tokens": pt, "cache_hit_tokens": hit,
               "completion_tokens": out, "usage_seen": bool(usage), "usd": round(usd, 6),
               "total_usd": round(STATE["total_usd"], 6), "seconds": round(seconds, 2)}
        with open(path, "a") as f:
            f.write(json.dumps(row) + "\n")
    return usd


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # quiet; the JSONL is the record
        pass

    def do_GET(self):
        if self.path == "/__status":
            body = json.dumps({**STATE, "cap_usd": ARGS.cap_usd}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        self._forward(b"")

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        self._forward(self.rfile.read(n) if n else b"")

    def _forward(self, body):
        with LOCK:
            over = STATE["total_usd"] >= ARGS.cap_usd
        if over:
            with LOCK:
                STATE["refused"] += 1
            msg = json.dumps({"error": {"message": f"block U cap {ARGS.cap_usd} USD reached at the proxy", "type": "budget"}}).encode()
            self.send_response(402); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg))); self.end_headers(); self.wfile.write(msg); return
        model, stream = "", False
        if body:
            try:
                j = json.loads(body); model = str(j.get("model", "")); stream = bool(j.get("stream"))
                if stream and isinstance(j, dict) and "stream_options" not in j:
                    j["stream_options"] = {"include_usage": True}; body = json.dumps(j).encode()
            except Exception:
                pass
        headers = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "content-length", "connection", "accept-encoding")}
        headers["Content-Length"] = str(len(body))
        req = urllib.request.Request(ARGS.upstream.rstrip("/") + self.path, data=body if body else None,
                                     headers=headers, method=self.command)
        t0 = time.time(); usage = None; status = 0
        try:
            resp = urllib.request.urlopen(req, timeout=ARGS.timeout)
        except urllib.error.HTTPError as e:
            resp = e
        except Exception as e:
            msg = json.dumps({"error": {"message": f"proxy upstream error: {e}"}}).encode()
            self.send_response(502); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg))); self.end_headers(); self.wfile.write(msg)
            record(ARGS.ledger, model, None, stream, 502, time.time() - t0, self.path); return
        status = resp.status if hasattr(resp, "status") else resp.code
        ctype = resp.headers.get("Content-Type", "")
        self.send_response(status)
        for k, v in resp.headers.items():
            if k.lower() in ("content-type", "cache-control", "x-request-id"):
                self.send_header(k, v)
        if stream and "text/event-stream" in ctype:
            self.send_header("Transfer-Encoding", "chunked"); self.end_headers()
            buf = b""
            try:
                while True:
                    chunk = resp.read1(65536) if hasattr(resp, "read1") else resp.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(b"%x\r\n%s\r\n" % (len(chunk), chunk)); self.wfile.flush()
                    buf += chunk
                    while b"\n\n" in buf:
                        ev, buf = buf.split(b"\n\n", 1)
                        for line in ev.split(b"\n"):
                            if line.startswith(b"data:") and b"usage" in line:
                                try:
                                    d = json.loads(line[5:].strip())
                                    u = d.get("usage") or (d.get("response") or {}).get("usage")
                                    if u:
                                        usage = u
                                except Exception:
                                    pass
                self.wfile.write(b"0\r\n\r\n"); self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            data = resp.read()
            self.send_header("Content-Length", str(len(data))); self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass
            try:
                d = json.loads(data); usage = d.get("usage") or None
                model = model or str(d.get("model", ""))
            except Exception:
                pass
        record(ARGS.ledger, model, usage, stream, status, time.time() - t0, self.path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787); ap.add_argument("--ledger", required=True)
    ap.add_argument("--cap-usd", type=float, required=True); ap.add_argument("--upstream", default="https://api.deepseek.com")
    ap.add_argument("--timeout", type=float, default=600)
    ARGS = ap.parse_args()
    try:  # the cap covers the whole block: start from what an earlier proxy process already spent
        for line in open(ARGS.ledger):
            STATE["total_usd"] += float(json.loads(line).get("usd") or 0); STATE["calls"] += 1
    except FileNotFoundError:
        pass
    print(f"deepseek_proxy on 127.0.0.1:{ARGS.port} -> {ARGS.upstream}, cap ${ARGS.cap_usd}, ledger {ARGS.ledger}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", ARGS.port), H).serve_forever()
