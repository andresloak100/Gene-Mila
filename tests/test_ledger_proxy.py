"""The ledger proxy (tools/baselines/ledger_proxy.py) against a mock upstream: it replaces the client's token with the
key from its own environment, prices OpenAI chat, OpenAI Responses and Anthropic usage (plain and SSE) with the lab's
table into a ledger with the lab's schema, logs the served model and never a body or a token, and refuses at the
session cap, at the block cap and on a usage shape it does not know; it asks the upstream for an uncompressed body,
prices a stream whose client went away, halts on a stream without its output usage (Anthropic without message_delta,
Responses without response.completed), reserves for calls in flight, and merges Biomni's consecutive assistant messages
only when asked."""
import gzip
import json
import socket
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
RS_USAGE = {"input_tokens": 100, "input_tokens_details": {"cached_tokens": 40}, "output_tokens": 20,
            "output_tokens_details": {"reasoning_tokens": 5}, "total_tokens": 120}  # the Responses API shape
PRICING = lp.load_pricing(ROOT / "configs" / "default.toml")


def responses_sse(served: str, usage: dict, completed: bool = True, final: str = "response.completed") -> str:
    """A Responses API stream as the upstream sends it: response.created, two response.output_text.delta events and,
    unless completed is False, the terminal event `final` (response.completed, or response.incomplete for a response
    stopped by max_output_tokens) with the final response object (usage inside it)."""
    resp = {"id": "resp_x", "object": "response", "model": served, "status": "in_progress", "output": []}
    delta = {"type": "response.output_text.delta", "item_id": "msg_x", "output_index": 0, "content_index": 0}
    events = [("response.created", {"type": "response.created", "sequence_number": 0, "response": resp}),
              ("response.output_text.delta", {**delta, "sequence_number": 1, "delta": SECRET_TEXT[:10]}),
              ("response.output_text.delta", {**delta, "sequence_number": 2, "delta": SECRET_TEXT[10:]})]
    if completed:
        done = {**resp, "status": final.split(".")[1], "usage": usage,
                "output": [{"type": "message", "id": "msg_x", "role": "assistant", "status": "completed",
                            "content": [{"type": "output_text", "text": SECRET_TEXT, "annotations": []}]}]}
        if final == "response.incomplete":
            done["incomplete_details"] = {"reason": "max_output_tokens"}
        events.append((final, {"type": final, "sequence_number": 3, "response": done}))
    return "".join(f"event: {e}\ndata: {json.dumps(d)}\n\n" for e, d in events)


class Upstream(BaseHTTPRequestHandler):
    """Canned DeepSeek: OpenAI chat completions, OpenAI Responses and Anthropic messages, plain or SSE; records what it
    received."""
    seen: list = []
    mode = "ok"  # or "nousage", "gzip" (compress when Accept-Encoding allows), "nodelta" (no message_delta),
    # "slow" (one SSE event every 0.2 s), "biomni" (an <execute> reply, then a <solution> once an observation is seen),
    # "nocached" (Responses usage without input_tokens_details), "nocompleted" (a Responses stream that ends without
    # response.completed), "incomplete" (a Responses stream that ends with response.incomplete, usage inside), "badtype"
    # (Responses usage whose counts are not integers: input_tokens an object when plain, cached_tokens a string in a
    # stream)

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
                              "x-api-key": self.headers.get("x-api-key"), "body": req,
                              "accept-encoding": self.headers.get("Accept-Encoding")})
        model = req.get("model")
        served = "deepseek-chat" if model == "deepseek-flash" else model  # the legacy name, as the real API does
        if self.path == "/v1/chat/completions":
            reply = SECRET_TEXT
            if Upstream.mode == "biomni":
                last = (req.get("messages") or [{}])[-1]  # Biomni appends the observation as an assistant message
                seen_obs = last.get("role") == "assistant" and str(last.get("content") or "").lstrip().startswith(
                    "<observation>")
                reply = "<solution>4</solution>" if seen_obs else "<execute>print(2 + 2)</execute>"
            doc = {"id": "x", "object": "chat.completion", "model": served, "usage": dict(OA_USAGE),
                   "choices": [{"index": 0, "message": {"role": "assistant", "content": reply},
                                "finish_reason": "stop"}]}
            if Upstream.mode == "nousage":
                doc["usage"] = {"tokens": 3}
            if Upstream.mode == "gzip" and "gzip" in (self.headers.get("Accept-Encoding") or ""):
                body = gzip.compress(json.dumps(doc).encode())
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Encoding", "gzip")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                return self.wfile.write(body)
            if req.get("stream"):
                chunks = [{"id": "x", "object": "chat.completion.chunk", "model": served,
                           "choices": [{"index": 0, "delta": {"content": SECRET_TEXT}}]},
                          {"id": "x", "object": "chat.completion.chunk", "model": served, "choices": [],
                           "usage": doc["usage"] if req.get("stream_options", {}).get("include_usage") else None}]
                body = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
                return self._send(200, "text/event-stream", body.encode())
            return self._send(200, "application/json", json.dumps(doc).encode())
        if self.path == "/v1/responses":
            usage = dict(RS_USAGE)
            if Upstream.mode == "nousage":
                usage = {"tokens": 3}
            if Upstream.mode == "nocached":
                usage = {k: v for k, v in RS_USAGE.items() if k != "input_tokens_details"}
            if Upstream.mode == "badtype":
                usage = ({**RS_USAGE, "input_tokens_details": {"cached_tokens": "n/a"}} if req.get("stream")
                         else {**RS_USAGE, "input_tokens": {"n": 100}})
            if req.get("stream"):
                final = "response.incomplete" if Upstream.mode == "incomplete" else "response.completed"
                body = responses_sse(served, usage, completed=Upstream.mode != "nocompleted", final=final)
                return self._send(200, "text/event-stream", body.encode())
            doc = {"id": "resp_x", "object": "response", "model": served, "status": "completed", "usage": usage,
                   "output": [{"type": "message", "id": "msg_x", "role": "assistant", "status": "completed",
                               "content": [{"type": "output_text", "text": SECRET_TEXT, "annotations": []}]}]}
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
                if Upstream.mode == "nodelta":
                    events = [ev for ev in events if ev[0] != "message_delta"]
                if Upstream.mode == "slow":  # close-delimited body, one event at a time
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.end_headers()
                    for e, d in events:
                        try:
                            self.wfile.write(f"event: {e}\ndata: {json.dumps(d)}\n\n".encode())
                            self.wfile.flush()
                        except OSError:
                            return
                        time.sleep(0.2)
                    return
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

    def start(session_cap=2.5, block_cap=100.0, ledger=None, arm="biomni", run_id="h_test_r7", merge=False):
        ledger = ledger or tmp_path / f"ledger{len(made)}.sqlite"
        p = lp.Proxy(upstream, ledger, run_id, arm, session_cap, block_cap, tmp_path / f"proxy{len(made)}.jsonl",
                     PRICING, KEY, merge_assistant=merge)
        srv = lp.make_server("127.0.0.1:0", p)
        _serve(srv)
        made.append(srv)
        return p, f"http://127.0.0.1:{srv.server_address[1]}"

    yield start
    for srv in made:
        srv.shutdown()


def post(base, path, body, token=DUMMY, header="Authorization", **headers):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          header: (f"Bearer {token}" if header == "Authorization" else token),
                                          **headers})
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


def test_responses_route_plain_and_sse_price_like_the_chat_route(proxy_factory):
    """The Codex CLI's wire format: POST /v1/responses forwarded to the upstream's /v1/responses with the key, no body
    edit; input_tokens minus cached_tokens as misses, cached_tokens as hits, output_tokens as output; the usage of a
    stream read from response.completed and the events relayed byte for byte."""
    p, base = proxy_factory(arm="autoresearch")
    Upstream.seen.clear()
    Upstream.mode = "ok"
    body = {"model": "deepseek-v4-pro", "instructions": "be brief", "input": "hi there"}
    status, _, data = post(base, "/v1/responses", body)
    assert status == 200 and json.loads(data)["output"][0]["content"][0]["text"] == SECRET_TEXT
    assert Upstream.seen[-1]["path"] == "/v1/responses" and Upstream.seen[-1]["auth"] == f"Bearer {KEY}"
    assert DUMMY not in (Upstream.seen[-1]["auth"] or "") and Upstream.seen[-1]["x-api-key"] is None
    assert Upstream.seen[-1]["body"] == body and Upstream.seen[-1]["accept-encoding"] == "identity"
    status, ctype, data = post(base, "/v1/responses", {**body, "stream": True})
    assert status == 200 and "text/event-stream" in ctype
    assert data == responses_sse("deepseek-v4-pro", RS_USAGE).encode()  # the events reach the client unchanged
    assert Upstream.seen[-1]["body"] == {**body, "stream": True}  # no include_usage injection on this route
    r = rows(p.ledger.path)
    assert len(r) == 2 and {x["role"] for x in r} == {"baseline:autoresearch"}
    assert {x["model"] for x in r} == {"deepseek-v4-pro"} and {x["run_id"] for x in r} == {"h_test_r7"}
    for x in r:
        assert (x["input_tokens"], x["cached_tokens"], x["output_tokens"]) == (100, 40, 20)
        assert x["cost_usd"] == pytest.approx(expected_cost("deepseek-v4-pro", 40, 60, 20))
    assert p.session_spent == pytest.approx(2 * expected_cost("deepseek-v4-pro", 40, 60, 20))
    lines = [ln for ln in log_lines(p) if ln.get("status") == 200]
    assert [ln["stream"] for ln in lines] == [False, True] and {ln["route"] for ln in lines} == {"/v1/responses"}
    assert all(ln["model_served"] == "deepseek-v4-pro" and ln["priced_as"] == "deepseek-v4-pro" for ln in lines)
    assert all("cached_tokens_absent" not in ln for ln in lines) and lines[1]["client_gone"] is False
    assert set(lines[0]) == {"ts", "run_id", "route", "model_requested", "model_served", "priced_as", "status", "stream",
                             "input_tokens", "cached_tokens", "output_tokens", "cost_usd", "latency_s",
                             "session_cost_usd", "ledger_total_usd"}
    raw = p.log_path.read_text()
    for forbidden in (KEY, DUMMY, "Bearer", SECRET_TEXT, "hi there", "be brief", "instructions", "resp_x", "msg_x"):
        assert forbidden not in raw, forbidden


def test_responses_usage_without_cached_tokens_prices_cached_as_zero_and_says_so(proxy_factory):
    """DeepSeek's field names on this route are unverified: a usage with input_tokens and output_tokens but no
    input_tokens_details is priced with every prompt token at the miss rate, and the log line says so."""
    p, base = proxy_factory()
    Upstream.mode = "nocached"
    try:
        s1, _, _ = post(base, "/v1/responses", {"model": "deepseek-v4-pro", "input": "hi"})
        s2, _, _ = post(base, "/v1/responses", {"model": "deepseek-v4-pro", "input": "hi", "stream": True})
    finally:
        Upstream.mode = "ok"
    assert (s1, s2) == (200, 200) and p.halted is None
    r = rows(p.ledger.path)
    assert len(r) == 2
    for x in r:
        assert (x["input_tokens"], x["cached_tokens"], x["output_tokens"]) == (100, 0, 20)
        assert x["cost_usd"] == pytest.approx(expected_cost("deepseek-v4-pro", 0, 100, 20))
    lines = [ln for ln in log_lines(p) if ln.get("status") == 200]
    assert len(lines) == 2 and all(ln["cached_tokens_absent"] is True and ln["cached_tokens"] == 0 for ln in lines)


def test_responses_unknown_usage_shape_gives_502_and_halts(proxy_factory):
    p, base = proxy_factory()
    Upstream.mode = "nousage"
    try:
        status, _, data = post(base, "/v1/responses", {"model": "deepseek-v4-pro", "input": "hi"})
        assert status == 502 and json.loads(data)["error"]["type"] == "unpriced_usage"
        bad = [ln for ln in log_lines(p) if ln.get("unpriced")]
        assert len(bad) == 1 and bad[0]["usage_keys"] == ["tokens"] and bad[0]["route"] == "/v1/responses"
        assert "input_tokens" in bad[0]["error"] and rows(p.ledger.path) == []
        # the same shape inside response.completed: relayed, unpriced, halted, the keys seen named
        p2, base2 = proxy_factory()
        status, _, data = post(base2, "/v1/responses", {"model": "deepseek-v4-pro", "input": "hi", "stream": True})
        assert status == 200 and b"response.completed" in data and rows(p2.ledger.path) == []
        bad = [ln for ln in log_lines(p2) if ln.get("unpriced")]
        assert len(bad) == 1 and bad[0]["usage_keys"] == ["tokens"] and bad[0]["stream"] is True
    finally:
        Upstream.mode = "ok"
    for b in (base, base2):
        status, _, data = post(b, "/v1/responses", {"model": "deepseek-v4-pro", "input": "hi"})
        assert status == 402 and "halted" in json.loads(data)["error"]["message"]
    assert not json.loads(urllib.request.urlopen(base + "/healthz", timeout=10).read())["ok"]


def test_responses_usage_with_a_count_that_is_not_an_integer_gives_502_and_halts(proxy_factory):
    """A field that is present with the wrong type (an object, a string) ends in the same unpriced path as a missing
    one: 502 (plain) or the relayed stream, the keys seen in the log line, the proxy halted; never a dead handler thread
    that leaves the call unpriced and the proxy admitting the next one."""
    p, base = proxy_factory()
    p2, base2 = proxy_factory()
    Upstream.mode = "badtype"
    try:
        status, _, data = post(base, "/v1/responses", {"model": "deepseek-v4-pro", "input": "hi"})
        assert status == 502 and json.loads(data)["error"]["type"] == "unpriced_usage"
        bad = [ln for ln in log_lines(p) if ln.get("unpriced")]
        assert len(bad) == 1 and bad[0]["usage_keys"] == sorted(RS_USAGE) and "input_tokens" in bad[0]["error"]
        status, _, data = post(base2, "/v1/responses", {"model": "deepseek-v4-pro", "input": "hi", "stream": True})
        assert status == 200 and b"response.completed" in data
        bad = [ln for ln in log_lines(p2) if ln.get("unpriced")]
        assert len(bad) == 1 and bad[0]["stream"] is True and "cached_tokens" in bad[0]["error"]
        assert bad[0]["usage_keys"] == sorted(RS_USAGE) and bad[0]["model_served"] == "deepseek-v4-pro"
    finally:
        Upstream.mode = "ok"
    for q, b in ((p, base), (p2, base2)):
        assert rows(q.ledger.path) == [] and "not an integer" in (q.halted or "")
        status, _, data = post(b, "/v1/responses", {"model": "deepseek-v4-pro", "input": "hi"})
        assert status == 402 and "halted" in json.loads(data)["error"]["message"]


def test_a_responses_stream_ending_in_response_incomplete_is_priced_and_says_so(proxy_factory):
    """max_output_tokens (or a filter) ends the stream with response.incomplete; its response object carries the final
    usage and DeepSeek has billed the call, so it is priced like a completed one and the log line says incomplete."""
    p, base = proxy_factory()
    Upstream.mode = "incomplete"
    try:
        status, _, data = post(base, "/v1/responses", {"model": "deepseek-v4-pro", "input": "hi", "stream": True})
    finally:
        Upstream.mode = "ok"
    assert status == 200 and data == responses_sse("deepseek-v4-pro", RS_USAGE, final="response.incomplete").encode()
    assert p.halted is None
    r = rows(p.ledger.path)
    assert len(r) == 1 and (r[0]["input_tokens"], r[0]["cached_tokens"], r[0]["output_tokens"]) == (100, 40, 20)
    assert r[0]["cost_usd"] == pytest.approx(expected_cost("deepseek-v4-pro", 40, 60, 20))
    lines = [ln for ln in log_lines(p) if ln.get("status") == 200]
    assert len(lines) == 1 and lines[0]["response_status"] == "incomplete" and lines[0]["stream"] is True
    status, _, _ = post(base, "/v1/responses", {"model": "deepseek-v4-pro", "input": "hi"})
    assert status == 200 and "response_status" not in [ln for ln in log_lines(p) if ln.get("status") == 200][1]


def test_a_responses_stream_without_response_completed_is_not_priced(proxy_factory):
    p, base = proxy_factory()
    Upstream.mode = "nocompleted"
    try:
        status, _, data = post(base, "/v1/responses", {"model": "deepseek-v4-pro", "input": "hi", "stream": True})
    finally:
        Upstream.mode = "ok"
    assert status == 200 and data == responses_sse("deepseek-v4-pro", RS_USAGE, completed=False).encode()  # relayed
    assert rows(p.ledger.path) == [] and "response.completed" in (p.halted or "")
    bad = [ln for ln in log_lines(p) if ln.get("unpriced")]
    assert len(bad) == 1 and bad[0]["stream"] is True and bad[0]["model_served"] == "deepseek-v4-pro"
    status, _, data = post(base, "/v1/responses", {"model": "deepseek-v4-pro", "input": "hi"})
    assert status == 402 and "halted" in json.loads(data)["error"]["message"]


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


def test_other_routes_are_refused_and_startup_needs_the_key_and_an_existing_ledger(proxy_factory, monkeypatch,
                                                                                    tmp_path, upstream):
    p, base = proxy_factory()
    status, _, data = post(base, "/v1/embeddings", {"model": "x", "input": "y"})
    assert status == 404 and rows(p.ledger.path) == []
    assert log_lines(p)[-1]["route"] == "/v1/embeddings" and log_lines(p)[-1]["status"] == 404
    argv = ["--ledger", str(tmp_path / "missing.sqlite"), "--run-id", "r", "--session-cap-usd", "1",
            "--block-cap-usd", "2", "--log", str(tmp_path / "l.jsonl"), "--upstream", upstream]
    with pytest.raises(SystemExit, match="does not exist"):  # a mistyped path would start an empty ledger
        lp.build(lp.parse(argv))
    monkeypatch.delenv(lp.KEY_ENV, raising=False)
    with pytest.raises(SystemExit, match=lp.KEY_ENV):
        lp.build(lp.parse(argv))
    for listen in ("0.0.0.0:8787", "[::1]:8787"):  # IPv6 loopback is not accepted: the server binds AF_INET
        assert lp.main(["--listen", listen, "--ledger", str(p.ledger.path), "--run-id", "r", "--session-cap-usd", "1",
                        "--block-cap-usd", "2", "--log", str(tmp_path / "l.jsonl")]) == 2


def test_upstream_is_asked_for_an_uncompressed_body(proxy_factory):
    """Both real clients ask for gzip; the proxy cannot read the usage of a compressed body, so it must not forward it."""
    p, base = proxy_factory()
    Upstream.seen.clear()
    Upstream.mode = "gzip"
    try:
        status, _, body = post(base, "/v1/chat/completions", {"model": "deepseek-v4-pro", "messages": []},
                               **{"Accept-Encoding": "gzip, deflate, zstd"})
    finally:
        Upstream.mode = "ok"
    assert status == 200 and json.loads(body)["choices"][0]["message"]["content"] == SECRET_TEXT
    assert Upstream.seen[-1]["accept-encoding"] == "identity"
    assert len(rows(p.ledger.path)) == 1 and p.halted is None


def test_a_stream_whose_client_goes_away_is_still_priced(proxy_factory):
    """Claude Code is killed at the wall clock with a request in flight; the upstream has billed it."""
    p, base = proxy_factory()
    Upstream.mode = "slow"
    try:
        host, port = base[len("http://"):].split(":")
        body = json.dumps({"model": "deepseek-v4-pro", "stream": True, "max_tokens": 8, "messages": []}).encode()
        with socket.create_connection((host, int(port)), timeout=10) as sock:
            sock.sendall(b"POST /anthropic/v1/messages HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n"
                         b"Authorization: Bearer " + DUMMY.encode() + b"\r\nContent-Length: " + str(len(body)).encode()
                         + b"\r\n\r\n" + body)
            first = sock.recv(4096)
        assert b"200" in first
        deadline = time.time() + 15
        while time.time() < deadline and not rows(p.ledger.path):
            time.sleep(0.2)
    finally:
        Upstream.mode = "ok"
    r = rows(p.ledger.path)
    assert len(r) == 1 and (r[0]["input_tokens"], r[0]["output_tokens"]) == (65, 7) and p.halted is None
    line = [ln for ln in log_lines(p) if ln.get("status") == 200][-1]
    assert line["stream"] and line["client_gone"] is True


def test_an_anthropic_stream_without_message_delta_is_not_priced(proxy_factory):
    p, base = proxy_factory()
    Upstream.mode = "nodelta"
    try:
        status, _, data = post(base, "/anthropic/v1/messages", {"model": "deepseek-v4-pro", "stream": True, "messages": []})
    finally:
        Upstream.mode = "ok"
    assert status == 200 and "message_stop" in data.decode()  # relayed; priced it is not
    assert rows(p.ledger.path) == [] and "message_delta" in (p.halted or "")
    status, _, data = post(base, "/anthropic/v1/messages", {"model": "deepseek-v4-pro", "messages": []})
    assert status == 402 and "halted" in json.loads(data)["error"]["message"]


def test_concurrent_requests_cannot_all_pass_the_session_cap(proxy_factory):
    one_call = expected_cost("deepseek-v4-pro", 40, 60, 20)
    p, base = proxy_factory(session_cap=1.5 * one_call)
    Upstream.mode = "slow"  # Anthropic streams of about 1.2 s, so the eight requests overlap
    results = []
    body = {"model": "deepseek-v4-pro", "stream": True, "max_tokens": 8, "messages": []}

    def one():
        results.append(post(base, "/anthropic/v1/messages", body)[0])

    try:
        threads = [threading.Thread(target=one) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
    finally:
        Upstream.mode = "ok"
    priced = len(rows(p.ledger.path))
    assert 1 <= priced <= 2, (priced, results)  # settled plus the in-flight reservation; never all eight
    assert results.count(200) == priced and results.count(402) == 8 - priced
    refused = [ln["refused"] for ln in log_lines(p) if ln.get("status") == 402]
    assert all("session cap" in why for why in refused) and any("in flight" in why for why in refused)
    assert p.inflight == 0


def test_consecutive_assistant_messages_are_merged_only_when_asked(proxy_factory):
    msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"},
            {"role": "assistant", "content": "<execute>print(2 + 2)</execute>"},
            {"role": "assistant", "content": "<observation>4</observation>"}, {"role": "user", "content": "go on"}]
    merged, n = lp.merge_consecutive_assistant(msgs)
    assert n == 1 and [m["role"] for m in merged] == ["system", "user", "assistant", "user"]
    assert merged[2]["content"] == "<execute>print(2 + 2)</execute>\n\n<observation>4</observation>"
    assert lp.merge_consecutive_assistant([{"role": "assistant", "content": [{"type": "text", "text": "a"}]},
                                           {"role": "assistant", "content": "b"}])[1] == 0  # only string content
    p, base = proxy_factory()
    Upstream.seen.clear()
    assert post(base, "/v1/chat/completions", {"model": "deepseek-v4-pro", "messages": msgs})[0] == 200
    assert len(Upstream.seen[-1]["body"]["messages"]) == 5 and "merged_messages" not in log_lines(p)[-1]
    p2, base2 = proxy_factory(merge=True)
    assert post(base2, "/v1/chat/completions", {"model": "deepseek-v4-pro", "messages": msgs})[0] == 200
    assert len(Upstream.seen[-1]["body"]["messages"]) == 4 and log_lines(p2)[-1]["merged_messages"] == 1


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
    u, extra = lp.usage_responses(RS_USAGE)
    assert (u.input_tokens, u.cached_tokens, u.output_tokens) == (100, 40, 20) and extra == {}
    u, extra = lp.usage_responses({"input_tokens": 10, "output_tokens": 2})
    assert (u.input_tokens, u.cached_tokens, u.output_tokens) == (10, 0, 2) and extra == {"cached_tokens_absent": True}
    with pytest.raises(lp.UnknownUsage):
        lp.usage_responses({"input_tokens": 10, "input_tokens_details": {"cached_tokens": 3}})
    with pytest.raises(lp.UnknownUsage):
        lp.usage_responses([1, 2])
    for bad in ({"input_tokens": [1], "output_tokens": 2}, {"input_tokens": 1, "output_tokens": "n/a"},
                {"input_tokens": 1, "output_tokens": 2, "input_tokens_details": {"cached_tokens": {"n": 1}}}):
        with pytest.raises(lp.UnknownUsage, match="not an integer"):
            lp.usage_responses(bad)
    with pytest.raises(lp.UnknownUsage, match="not an integer"):
        lp.usage_openai({"prompt_tokens": "x", "completion_tokens": 1})
    assert lp.price_key(PRICING, "deepseek-v4-pro", "something-new") == "deepseek-v4-pro"
    assert lp.price_key(PRICING, "unknown", None) == "default"
    assert time.time() > 0
