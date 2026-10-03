import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from genemila.config import load_config
from genemila.db import Database
from genemila.llm import BudgetExceeded, LLMGateway, SpendLedger, TokenLimitExceeded
from genemila.planner import parse_json
from genemila.providers import make_provider
from genemila.providers.base import AgentProvider, LLMResponse, ProviderError, Usage
from genemila.providers.openai_compat import DeepSeekProvider, OpenAICompatProvider


class FixedProvider(AgentProvider):
    name = "deepseek"

    def __init__(self, in_tok=1000, out_tok=500, fail=None):
        super().__init__("deepseek-chat")
        self.in_tok, self.out_tok, self.fail, self.calls = in_tok, out_tok, fail, 0

    def complete(self, system, user, max_tokens):
        self.calls += 1
        if self.fail:
            raise ProviderError(self.fail, retryable=True)
        return LLMResponse("ok", Usage(self.in_tok, self.out_tok, cached_tokens=200), "deepseek", "deepseek-chat")


def gateway(tmp_path, **budget):
    cfg = load_config()
    cfg["budget"].update(budget)
    db = Database(tmp_path / "g.db")
    return LLMGateway(db, cfg, "r", SpendLedger(tmp_path / "ledger.sqlite")), db


def test_cost_tracking(tmp_path):
    gw, db = gateway(tmp_path)
    resp = gw.call(FixedProvider(), "complete", role="worker", max_tokens=500, est_input_tokens=1000,
                   experiment_id=None, system="s", user="u")
    expected = (200 * 0.028 + 800 * 0.28 + 500 * 0.42) / 1e6
    assert gw.cost("deepseek-chat", resp.usage) == pytest.approx(expected)
    t = db.llm_totals()
    assert (t["input_tokens"], t["output_tokens"], t["cached_tokens"]) == (1000, 500, 200)
    assert t["cost_usd"] == pytest.approx(expected)


def test_hard_budget_halts_new_calls(tmp_path):
    gw, _ = gateway(tmp_path, max_total_usd=0.0005)
    p = FixedProvider()
    n = 0
    with pytest.raises(BudgetExceeded):
        for _ in range(100):
            gw.call(p, "complete", role="worker", max_tokens=500, est_input_tokens=1000, system="s", user="u")
            n += 1
    calls_at_halt = p.calls
    with pytest.raises(BudgetExceeded):
        gw.call(p, "complete", role="worker", max_tokens=1, est_input_tokens=1, system="s", user="u")
    assert p.calls == calls_at_halt  # refused before reaching the provider
    assert gw.spent["worker"] <= 0.0005


def test_cumulative_ledger_cap_survives_runs(tmp_path):
    gw1, _ = gateway(tmp_path, cumulative_usd={"deepseek": 0.001})
    p = FixedProvider()
    with pytest.raises(BudgetExceeded):
        for _ in range(100):
            gw1.call(p, "complete", role="worker", max_tokens=500, est_input_tokens=1000, system="s", user="u")
    gw2, _ = gateway(tmp_path, cumulative_usd={"deepseek": 0.001})  # "next run" sharing the ledger
    with pytest.raises(BudgetExceeded):
        gw2.call(p, "complete", role="worker", max_tokens=500, est_input_tokens=1000, system="s", user="u")


def test_token_limits(tmp_path):
    gw, _ = gateway(tmp_path, max_tokens_per_experiment=3000, max_tokens_per_worker=100000)
    p = FixedProvider()
    gw.call(p, "complete", role="worker", max_tokens=500, est_input_tokens=1000, experiment_id="E1",
            worker_id="W1", system="s", user="u")
    gw.call(p, "complete", role="worker", max_tokens=500, est_input_tokens=1000, experiment_id="E1",
            worker_id="W1", system="s", user="u")
    with pytest.raises(TokenLimitExceeded):
        gw.call(p, "complete", role="worker", max_tokens=500, est_input_tokens=1000, experiment_id="E1",
                worker_id="W1", system="s", user="u")


def test_bounded_retries_and_circuit_breaker(tmp_path):
    gw, db = gateway(tmp_path, api_retries=1, circuit_breaker_failures=4)
    p = FixedProvider(fail="HTTP 503")
    for _ in range(2):
        with pytest.raises(ProviderError):
            gw.call(p, "complete", role="worker", max_tokens=5, est_input_tokens=5, system="s", user="u")
    assert p.calls == 4  # 2 calls x (1 + 1 retry), never more
    with pytest.raises(BudgetExceeded, match="circuit breaker"):
        gw.call(p, "complete", role="worker", max_tokens=5, est_input_tokens=5, system="s", user="u")
    assert p.calls == 4
    assert db.llm_totals()["failed_calls"] == 4


class FakeOpenAI(BaseHTTPRequestHandler):
    seen_auth = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeOpenAI.seen_auth.append(self.headers.get("Authorization"))
        if body["model"] == "bad":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"error": {"message": "invalid key"}}')
            return
        out = {"model": body["model"], "choices": [{"message": {"content": "```python\nx=1\n```"}}],
               "usage": {"prompt_tokens": 120, "completion_tokens": 30, "prompt_cache_hit_tokens": 100}}
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(out).encode())

    def log_message(self, *a):
        pass


@pytest.fixture
def fake_server():
    srv = HTTPServer(("127.0.0.1", 0), FakeOpenAI)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def test_openai_compatible_provider_parses_usage_and_hides_key(fake_server, monkeypatch):
    monkeypatch.setenv("FAKE_KEY", "sk-secret-123")
    p = OpenAICompatProvider("m1", fake_server, "FAKE_KEY", name="fake")
    r = p.implement({"experiment_id": "E", "hypothesis": "h", "rationale": "r", "data_summary": "d",
                     "knowledge_summary": "k", "existing_features": "",
                     "new_feature": {"name": "f", "description": "d"}}, max_tokens=50)
    assert (r.usage.input_tokens, r.usage.output_tokens, r.usage.cached_tokens) == (120, 30, 100)
    assert FakeOpenAI.seen_auth[-1] == "Bearer sk-secret-123"
    bad = OpenAICompatProvider("bad", fake_server, "FAKE_KEY", name="fake")
    with pytest.raises(ProviderError) as ei:
        bad.complete("s", "u", 5)
    assert "sk-secret" not in str(ei.value) and not ei.value.retryable
    assert "sk-secret" not in repr(p.__dict__)


def test_deepseek_without_key_is_not_retryable(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    p = DeepSeekProvider()
    assert not p.available()
    with pytest.raises(ProviderError) as ei:
        p.complete("s", "u", 5)
    assert not ei.value.retryable


def test_provider_factory_and_interface():
    for kind, model in [("mock", "mock"), ("scripted", "scripted"), ("deepseek", "deepseek-chat"),
                        ("claude_cli", "opus"), ("anthropic", "claude-opus-5-5")]:
        p = make_provider(kind, model, {})
        assert isinstance(p, AgentProvider)
        for op in ("propose", "implement", "diagnose", "summarize"):
            assert callable(getattr(p, op))


def test_planner_json_parsing():
    assert parse_json('blah ```json\n{"a": 1}\n``` tail') == {"a": 1}
    assert parse_json('Here: {"hypotheses": []}') == {"hypotheses": []}
    with pytest.raises(ValueError):
        parse_json("no json here")
