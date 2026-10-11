"""The planner fallback chain: a failing LLM planner is replaced by the next entry for the rest of the run,
the switch is recorded, the run is labelled a mixed-planner arm, and an exhausted chain never degrades
silently to the scripted planner."""
import json

import pytest

from genemila.benchmark.table import run_arm
from genemila.controller import Controller, planner_fallbacks
from genemila.planner import PARSE_FAILURES_BEFORE_SWITCH, Planner
from genemila.providers.base import AgentProvider, LLMResponse, ProviderError
from genemila.providers.mock import MockProvider, ScriptedPlanner


class DownPlanner(AgentProvider):
    """An LLM planner whose usage limit is spent: every call fails without retry."""
    name = "claude_cli"

    def __init__(self, model="opus", text=None):
        super().__init__(model)
        self.calls = 0
        self.text = text

    def complete(self, system, user, max_tokens):
        self.calls += 1
        if self.text is not None:
            return LLMResponse(text=self.text, provider=self.name, model=self.model)
        raise ProviderError("usage limit reached; resets in 4h", retryable=False)


def test_failed_planner_switches_to_the_next_in_the_chain_for_good(lab_factory):
    lab = lab_factory()
    down, scripted = DownPlanner(), ScriptedPlanner()
    planner = Planner(lab, down, [scripted])
    assert planner.refill(3), "the fallback should have produced a plan in the same round"
    assert planner.provider is scripted and planner.switches and planner.switches[0]["from"] == "claude_cli:opus"
    assert planner.refill(3) and down.calls == 1, "the switch is sticky: the failed planner is not asked again"
    kinds = [e["kind"] for e in lab.db.query("SELECT kind FROM events ORDER BY id")]
    assert kinds.count("planner_switch") == 1 and "planner_error" in kinds and "planner_exhausted" not in kinds
    rounds = lab.db.query("SELECT provider FROM planner_rounds")
    assert rounds and all(r["provider"] == "scripted" for r in rounds)
    assert not planner.dry()


def test_exhausted_chain_stops_planning_without_a_scripted_stand_in(lab_factory):
    lab = lab_factory()
    down = DownPlanner()
    planner = Planner(lab, down)  # no fallback: the default for an LLM arm
    assert planner.refill(3) == [] and planner.exhausted and planner.dry()
    assert planner.refill(3) == [] and down.calls == 1, "an exhausted chain is not retried every round"
    kinds = [e["kind"] for e in lab.db.query("SELECT kind FROM events")]
    assert "planner_exhausted" in kinds and not lab.db.query("SELECT 1 FROM planner_rounds")


def test_malformed_plans_switch_only_when_repeated(lab_factory):
    lab = lab_factory()
    garbled, scripted = DownPlanner(text="no json here"), ScriptedPlanner()
    planner = Planner(lab, garbled, [scripted])
    for i in range(PARSE_FAILURES_BEFORE_SWITCH - 1):
        assert planner.refill(2) == [] and planner.provider is garbled
    assert planner.refill(2) and planner.provider is scripted
    assert garbled.calls == PARSE_FAILURES_BEFORE_SWITCH


def test_unusable_planner_is_skipped_at_start(lab_factory):
    lab = lab_factory()

    class Absent(DownPlanner):
        def available(self):
            return False

    planner = Planner(lab, Absent(), [Absent(model="also-absent"), ScriptedPlanner()])
    assert planner.provider.name == "scripted" and len(planner.switches) == 1
    assert sum(e["kind"] == "planner_switch" for e in lab.db.query("SELECT kind FROM events")) == 2  # one skip, one switch


def test_fallback_chain_parses_lists_and_strings():
    base = {"planner": {"provider": "claude_cli", "model": "opus", "timeout_s": 10}, "providers": {}}
    assert planner_fallbacks(base) == []
    assert [p.name for p in planner_fallbacks({**base, "planner": {**base["planner"], "fallback": "scripted"}})] == ["scripted"]
    chain = planner_fallbacks({**base, "planner": {**base["planner"], "fallback": "deepseek:deepseek-v4-pro, scripted"}})
    assert [(p.name, p.model) for p in chain] == [("deepseek", "deepseek-v4-pro"), ("scripted", "scripted")]
    chain = planner_fallbacks({**base, "planner": {**base["planner"], "fallback": ["loadtest:x", "none"]}})
    assert [p.name for p in chain] == ["loadtest"]
    with pytest.raises(ValueError):
        planner_fallbacks({**base, "planner": {**base["planner"], "fallback": "deepseek"}})


def test_mixed_planner_run_is_its_own_arm(lab_factory):
    lab = lab_factory(schedule__max_planner_calls=2, planner__provider="claude_cli", planner__model="opus")
    ctl = Controller(lab, workers=2, seconds=40, worker_provider=MockProvider(), planner_provider=DownPlanner(),
                     planner_fallback=[ScriptedPlanner()], quiet=True)
    summary = ctl.run()
    ph = summary["planner"]
    assert ph["mixed"] and ph["configured"] == "claude_cli:opus" and ph["used"] == ["scripted:scripted"]
    assert len(ph["switches"]) == 1 and ph["failed_rounds"] >= 1 and ph["exhausted_at_min"] is None
    cfg = {"planner": {"provider": "claude_cli", "model": "opus"}, "worker": {"provider": "mock", "model": "mock"}}
    assert run_arm(cfg) == "claude_cli:opus planner, mock:mock workers"
    assert run_arm(cfg, summary) == "claude_cli:opus -> scripted:scripted planner, mock:mock workers"
    assert "PLANNER CHANGED DURING THE RUN" in (lab.run_dir / "summary.md").read_text()
    assert json.loads((lab.run_dir / "summary.json").read_text())["planner"]["mixed"]


def test_run_that_lost_its_planner_is_labelled(lab_factory):
    lab = lab_factory(planner__provider="claude_cli", planner__model="opus")
    ctl = Controller(lab, workers=2, seconds=30, worker_provider=MockProvider(), planner_provider=DownPlanner(),
                     quiet=True)
    summary = ctl.run()
    ph = summary["planner"]
    assert ph["mixed"] and ph["used"] == [] and ph["exhausted_at_min"] is not None
    cfg = {"planner": {"provider": "claude_cli", "model": "opus"}, "worker": {"provider": "deepseek", "model": "v4"}}
    assert run_arm(cfg, summary) == "claude_cli:opus planner, deepseek:v4 workers (lost its planner)"
