"""The ledger proxy (tools/baselines/ledger_proxy.py) against a mock upstream: it replaces the client's token with the
key from its own environment, prices OpenAI and Anthropic usage (plain and SSE) with the lab's table into a ledger
with the lab's schema, logs the served model and never a body or a token, and refuses at the session cap, at the block
cap and on a usage shape it does not know."""
import json
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "baselines"))
import ledger_proxy as lp  # noqa: E402

KEY = "test-key-not-a-real-key-0123456789"
DUMMY = "proxy-token-7"
SECRET_TEXT = "the quick brown reply that must never be logged"
OA_USAGE = {"prompt_tokens": 100, "completion_tokens": 20, "prompt_cache_hit_tokens": 40, "prompt_cache_miss_tokens": 60,
            "total_tokens": 120}
AN_USAGE = {"input_tokens": 10, "cache_read_input_tokens": 50, "cache_creation_input_tokens": 5, "output_tokens": 7}
PRICING = lp.load_pricing(ROOT / "configs" / "default.toml")


class Upstream(BaseHTTPRequestHandler):
    """Canned DeepSeek: OpenAI chat completions and Anthropic messages, plain or SSE; records what it received."""
    seen: list = []
    mode = "ok"  # or "nousage"

    def log_message(self, *a):
        pass

    def _send(self, status, ctype, body: bytes):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        req = json.loads(self.rfile.read(n) or b"{}")
        Upstream.seen.append({"path": self.path, "auth": self.headers.get("Authorization"),
                              "x-api-key": self.headers.get("x-api-key"), "body": req})
        model = req.get("model")
        served = "deepseek-chat" if model == "deepseek-flash" else model  # the legacy name, as the real API does
        if self.path == "/v1/chat/completions":
            doc = {"id": "x", "object": "chat.completion", "model": served, "usage": dict(OA_USAGE),
                   "choices": [{"index": 0, "message": {"role": "assistant", "content": SECRET_TEXT},
                                "finish_reason": "stop"}]}
            if Upstream.mode == "nousage":
                doc["usage"] = {"tokens": 3}
            if req.get("stream"):
                chunks = [{"id": "x", "object": "chat.completion.chunk", "model": served,
                           "choices": [{"index": 0, "delta": {"content": SECRET_TEXT}}]},
                          {"id": "x", "object": "chat.completion.chunk", "model": served, "choices": [],
                           "usage": doc["usage"] if req.get("stream_options", {}).get("include_usage") else None}]
                body = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
                return self._send(200, "text/event-stream", body.encode())
            return self._send(200, "application/json", json.dumps(doc).encode())
        if self.path == "/anthropic/v1/messages":
            if req.get("stream"):
                events = [("message_start", {"type": "message_start", "message": {
                    "id": "m", "type": "message", "role": "assistant", "model": served, "content": [],
                    "usage": {k: v for k, v in AN_USAGE.items() if k != "output_tokens"} | {"output_tokens": 1}}}),
                          ("content_block_start", {"type": "content_block_start", "index": 0,
                                                   "content_block": {"type": "text", "text": ""}}),
                          ("content_block_delta", {"type": "content_block_delta", "index": 0,
                                                   "delta": {"type": "text_delta", "text": SECRET_TEXT}}),
                          ("content_block_stop", {"type": "content_block_stop", "index": 0}),
                          ("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn"},
                                             "usage": {"output_tokens": AN_USAGE["output_tokens"]}}),
                          ("message_stop", {"type": "message_stop"})]
                body = "".join(f"event: {e}\ndata: {json.dumps(d)}\n\n" for e, d in events)
                return self._send(200, "text/event-stream", body.encode())
            doc = {"id": "m", "type": "message", "role": "assistant", "model": served,
                   "content": [{"type": "text", "text": SECRET_TEXT}], "stop_reason": "end_turn",
                   "usage": dict(AN_USAGE)}
            return self._send(200, "application/json", json.dumps(doc).encode())
        self._send(404, "application/json", b'{"error": "no"}')


def _serve(server):
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return t


@pytest.fixture(scope="module")
def upstream():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    _serve(srv)
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


@pytest.fixture
def proxy_factory(upstream, tmp_path, monkeypatch):
    monkeypatch.setenv(lp.KEY_ENV, KEY)
    made = []

    def start(session_cap=2.5, block_cap=100.0, ledger=None, arm="biomni", run_id="h_test_r7"):
        ledger = ledger or tmp_path / f"ledger{len(made)}.sqlite"
        p = lp.Proxy(upstream, ledger, run_id, arm, session_cap, block_cap, tmp_path / f"proxy{len(made)}.jsonl",
                     PRICING, KEY)
        srv = lp.make_server("127.0.0.1:0", p)
        _serve(srv)
        made.append(srv)
        return p, f"http://127.0.0.1:{srv.server_address[1]}"

    yield start
    for srv in made:
        srv.shutdown()


def post(base, path, body, token=DUMMY, header="Authorization"):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          header: (f"Bearer {token}" if header == "Authorization" else token)})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), e.read()


def rows(ledger):
    with sqlite3.connect(ledger) as c:
        cols = [r[1] for r in c.execute("PRAGMA table_info(spend)")]
        return [dict(zip(cols, r)) for r in c.execute("SELECT * FROM spend ORDER BY ts")]


def log_lines(p):
    return [json.loads(ln) for ln in p.log_path.read_text().splitlines()]


def expected_cost(model, cached, miss, out):
    pr = PRICING[model]
    return (cached * pr["input_cache_hit"] + miss * pr["input_cache_miss"] + out * pr["output"]) / 1e6


def test_openai_route_replaces_the_token_and_writes_the_lab_ledger_row(proxy_factory):
    p, base = proxy_factory()
    Upstream.seen.clear()
    Upstream.mode = "ok"
    status, _, body = post(base, "/v1/chat/completions",
                           {"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hi"}]})
    assert status == 200 and json.loads(body)["choices"][0]["message"]["content"] == SECRET_TEXT
    assert Upstream.seen[-1]["auth"] == f"Bearer {KEY}" and DUMMY not in (Upstream.seen[-1]["auth"] or "")
    r = rows(p.ledger.path)
    assert len(r) == 1
    assert set(r[0]) == {"ts", "run_id", "provider", "model", "role", "input_tokens", "output_tokens", "cached_tokens",
                         "cost_usd"}  # genemila.llm.SpendLedger's schema
    assert r[0]["provider"] == "deepseek" and r[0]["model"] == "deepseek-v4-pro" and r[0]["role"] == "baseline:biomni"
    assert r[0]["run_id"] == "h_test_r7"
    assert (r[0]["input_tokens"], r[0]["cached_tokens"], r[0]["output_tokens"]) == (100, 40, 20)
    assert r[0]["cost_usd"] == pytest.approx(expected_cost("deepseek-v4-pro", 40, 60, 20))
    assert p.session_spent == pytest.approx(r[0]["cost_usd"]) and p.ledger_total == pytest.approx(r[0]["cost_usd"])
    # the ledger total the lab reads agrees
    from genemila.llm import SpendLedger
    assert SpendLedger(p.ledger.path).total("deepseek") == pytest.approx(r[0]["cost_usd"])


def test_anthropic_route_plain_and_sse_price_the_cache_fields_like_the_lab(proxy_factory):
    p, base = proxy_factory(arm="autoresearch")
    Upstream.seen.clear()
    body = {"model": "deepseek-v4-pro", "max_tokens": 64, "messages": [{"role": "user", "content": "hi"}]}
    status, _, data = post(base, "/anthropic/v1/messages", body, header="x-api-key")
    assert status == 200 and json.loads(data)["content"][0]["text"] == SECRET_TEXT
    assert Upstream.seen[-1]["auth"] == f"Bearer {KEY}" and Upstream.seen[-1]["x-api-key"] == KEY
    status, ctype, data = post(base, "/anthropic/v1/messages", {**body, "stream": True})
    assert status == 200 and "text/event-stream" in ctype
    text = data.decode()
    assert "event: message_start" in text and "event: message_stop" in text and SECRET_TEXT in text  # relayed whole
    r = rows(p.ledger.path)
    assert len(r) == 2 and {x["role"] for x in r} == {"baseline:autoresearch"}
    for x in r:  # input = input_tokens + cache read + cache creation; cached = reads (genemila/providers/anthropic_api)
        assert (x["input_tokens"], x["cached_tokens"], x["output_tokens"]) == (65, 50, 7)
        assert x["cost_usd"] == pytest.approx(expected_cost("deepseek-v4-pro", 50, 15, 7))
    lines = [ln for ln in log_lines(p) if ln.get("status") == 200]
    assert [ln["stream"] for ln in lines] == [False, True]
    assert all(ln["model_served"] == "deepseek-v4-pro" for ln in lines)


def test_openai_stream_gets_usage_injected_and_priced(proxy_factory):
    p, base = proxy_factory()
    Upstream.seen.clear()
    status, ctype, data = post(base, "/v1/chat/completions",
                               {"model": "deepseek-v4-pro", "stream": True, "messages": [{"role": "user", "content": "x"}]})
    assert status == 200 and "text/event-stream" in ctype and "data: [DONE]" in data.decode()
    assert Upstream.seen[-1]["body"]["stream_options"] == {"include_usage": True}
    assert len(rows(p.ledger.path)) == 1 and rows(p.ledger.path)[0]["output_tokens"] == 20


def test_log_has_no_bodies_and_no_tokens_and_names_the_served_model(proxy_factory):
    p, base = proxy_factory()
    post(base, "/v1/chat/completions", {"model": "deepseek-flash", "messages": [{"role": "user", "content": "hello"}]})
    raw = p.log_path.read_text()
    for forbidden in (KEY, DUMMY, "Bearer", SECRET_TEXT, "hello", "messages"):
        assert forbidden not in raw, forbidden
    call = [ln for ln in log_lines(p) if ln.get("status") == 200][0]
    assert call["route"] == "/v1/chat/completions" and call["model_requested"] == "deepseek-flash"
    assert call["model_served"] == "deepseek-chat" and call["priced_as"] == "deepseek-chat"  # the served name wins
    assert set(call) == {"ts", "run_id", "route", "model_requested", "model_served", "priced_as", "status", "stream",
                         "input_tokens", "cached_tokens", "output_tokens", "cost_usd", "latency_s",
                         "session_cost_usd", "ledger_total_usd"}
    assert call["cost_usd"] == pytest.approx(expected_cost("deepseek-chat", 40, 60, 20), abs=1e-8)
    assert rows(p.ledger.path)[0]["model"] == "deepseek-chat"


def test_session_cap_refuses_with_402(proxy_factory):
    one_call = expected_cost("deepseek-v4-pro", 40, 60, 20)
    p, base = proxy_factory(session_cap=1.5 * one_call)
    body = {"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hi"}]}
    assert post(base, "/v1/chat/completions", body)[0] == 200
    assert post(base, "/v1/chat/completions", body)[0] == 200  # settled spend (one call) is still under the cap
    status, _, data = post(base, "/v1/chat/completions", body)
    assert status == 402 and json.loads(data)["error"]["type"] == "budget_cap"
    assert "session cap" in json.loads(data)["error"]["message"]
    assert len(rows(p.ledger.path)) == 2
    refused = [ln for ln in log_lines(p) if ln.get("status") == 402]
    assert len(refused) == 1 and "session cap" in refused[0]["refused"]
    health = json.loads(urllib.request.urlopen(base + "/healthz", timeout=10).read())
    assert health["ok"] and health["calls"] == 2 and health["session_cost_usd"] == pytest.approx(2 * one_call, abs=1e-6)


def test_block_cap_counts_the_whole_ledger_plus_the_sessions_allowance(proxy_factory, tmp_path):
    from genemila.llm import SpendLedger
    from genemila.providers.base import Usage
    ledger = tmp_path / "shared.sqlite"
    SpendLedger(ledger).add("earlier_run", "deepseek", "deepseek-flash", "worker", Usage(10, 10, 0), 48.0)
    # ledger 48 + session cap 2.5 > block cap 50: refused before the first call
    p, base = proxy_factory(session_cap=2.5, block_cap=50.0, ledger=ledger)
    body = {"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hi"}]}
    status, _, data = post(base, "/anthropic/v1/messages", body)
    assert status == 402 and "block cap" in json.loads(data)["error"]["message"]
    assert len(rows(ledger)) == 1
    # ledger 48 + 2.5 <= 50.5: allowed; then another run writes to the ledger and the next call is refused
    p2, base2 = proxy_factory(session_cap=2.5, block_cap=50.5, ledger=ledger)
    assert post(base2, "/anthropic/v1/messages", body)[0] == 200
    SpendLedger(ledger).add("other_run", "deepseek", "deepseek-flash", "worker", Usage(10, 10, 0), 1.0)
    status, _, data = post(base2, "/anthropic/v1/messages", body)
    assert status == 402 and "block cap" in json.loads(data)["error"]["message"]
    assert p2.ledger_total == pytest.approx(SpendLedger(ledger).total("deepseek"))


def test_unknown_usage_shape_gives_502_and_halts(proxy_factory):
    p, base = proxy_factory()
    Upstream.mode = "nousage"
    try:
        body = {"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": "hi"}]}
        status, _, data = post(base, "/v1/chat/completions", body)
        assert status == 502 and json.loads(data)["error"]["type"] == "unpriced_usage"
        bad = [ln for ln in log_lines(p) if ln.get("unpriced")]
        assert len(bad) == 1 and bad[0]["usage_keys"] == ["tokens"] and bad[0]["status"] == 502
        assert rows(p.ledger.path) == []
    finally:
        Upstream.mode = "ok"
    status, _, data = post(base, "/v1/chat/completions", body)  # nothing more goes out: the spend is unbounded
    assert status == 402 and "halted" in json.loads(data)["error"]["message"]
    assert not json.loads(urllib.request.urlopen(base + "/healthz", timeout=10).read())["ok"]


def test_other_routes_are_refused_and_startup_needs_the_key(proxy_factory, monkeypatch, tmp_path, upstream):
    p, base = proxy_factory()
    status, _, data = post(base, "/v1/embeddings", {"model": "x", "input": "y"})
    assert status == 404 and rows(p.ledger.path) == []
    assert log_lines(p)[-1]["route"] == "/v1/embeddings" and log_lines(p)[-1]["status"] == 404
    monkeypatch.delenv(lp.KEY_ENV, raising=False)
    args = lp.parse(["--ledger", str(tmp_path / "l.sqlite"), "--run-id", "r", "--session-cap-usd", "1",
                     "--block-cap-usd", "2", "--log", str(tmp_path / "l.jsonl"), "--upstream", upstream])
    with pytest.raises(SystemExit, match=lp.KEY_ENV):
        lp.build(args)
    assert lp.main(["--listen", "0.0.0.0:8787", "--ledger", str(tmp_path / "l.sqlite"), "--run-id", "r",
                    "--session-cap-usd", "1", "--block-cap-usd", "2", "--log", str(tmp_path / "l.jsonl")]) == 2


def test_usage_parsers():
    u = lp.usage_openai(OA_USAGE)
    assert (u.input_tokens, u.cached_tokens, u.output_tokens) == (100, 40, 20)
    u = lp.usage_anthropic({"input_tokens": 10, "cache_read_input_tokens": 50, "cache_creation_input_tokens": 5},
                           {"output_tokens": 7})
    assert (u.input_tokens, u.cached_tokens, u.output_tokens) == (65, 50, 7)
    with pytest.raises(lp.UnknownUsage):
        lp.usage_openai({"prompt_tokens": 1})
    with pytest.raises(lp.UnknownUsage):
        lp.usage_openai({"prompt_tokens": 10, "completion_tokens": 1, "prompt_cache_hit_tokens": 3,
                         "prompt_cache_miss_tokens": 3})
    with pytest.raises(lp.UnknownUsage):
        lp.usage_anthropic({"input_tokens": 1}, None)
    assert lp.price_key(PRICING, "deepseek-v4-pro", "something-new") == "deepseek-v4-pro"
    assert lp.price_key(PRICING, "unknown", None) == "default"
    assert time.time() > 0
