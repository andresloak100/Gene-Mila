import json
import threading
import time

import pytest

from genemila.controller import Controller
from genemila.planner import Planner
from genemila.providers.mock import MockProvider, ScriptedPlanner
from genemila.spec import ExperimentSpec
from genemila.worker import Worker

BASE = ["control_mean", "mean_response", "is_target"]


def new_feature_spec(name, hint, **kw):
    return ExperimentSpec(hypothesis=f"Feature {name} improves held-out prediction.",
                          scientific_rationale="Biologically motivated test fixture rationale.",
                          kind="new_feature", category="explore", feature_set=BASE + [name],
                          proposed_feature={"name": name, "description": hint, "implementation_hint": hint},
                          hyperparameters={"alpha_grid": [1.0, 10.0]}, **kw)


def run_one(lab, spec, provider=None, escalation=None):
    eid, status = lab.queue(spec)
    assert status == "queued", lab.db.get_experiment(eid)
    w = Worker(lab, "W0", provider or MockProvider(), escalation, threading.Semaphore(2))
    rec = lab.db.claim_next("W0")
    w.process(rec)
    return lab.db.get_experiment(eid)


def test_full_experiment_records_everything(lab_factory):
    lab = lab_factory()
    rec = run_one(lab, new_feature_spec("coexpr", "co-expression with target"))
    assert rec["status"] == "completed", rec["failure_reason"]
    for key in ("primary_score", "cpu_s", "wall_s", "peak_rss_mb", "code_commit", "code_hash", "artifact_dir",
                "best_alpha", "timing_json", "model_size_bytes", "provider", "model", "split_id", "dataset"):
        assert rec[key] is not None, key
    assert rec["files_changed_json"] == [f"genemila/features/plugins/{rec['new_feature']}.py"]
    assert lab.db.feature(rec["new_feature"])["creator_experiment"] == rec["experiment_id"]
    assert rec["llm_calls"] == 1


def test_retry_then_success(lab_factory):
    rec = run_one(lab_factory(), new_feature_spec("fixme", "co-expression MOCK_BREAK"))
    assert rec["status"] == "completed"
    assert rec["llm_calls"] == 2


def test_persistent_failure_is_bounded_and_escalates(lab_factory):
    lab = lab_factory()
    class Strong(MockProvider):  # a stronger model that can fix what the cheap one cannot
        name = "escalated"

        def diagnose(self, task, code, error, max_tokens):
            nf = {k: v.replace("MOCK_BREAK_ALWAYS", "") if isinstance(v, str) else v
                  for k, v in task["new_feature"].items()}
            return super().diagnose({**task, "new_feature": nf}, code, error, max_tokens)

    esc = Strong(model="strong")
    rec = run_one(lab, new_feature_spec("hopeless", "MOCK_BREAK_ALWAYS variance"), escalation=esc)
    # cheap model: implement + 1 diagnose; escalation: 1 diagnose (mock fixes it)
    assert rec["escalated"] == 1
    assert rec["status"] == "completed" and rec["provider"] == "escalated"
    rec2 = run_one(lab, new_feature_spec("hopeless2", "MOCK_BREAK_ALWAYS variance"))
    assert rec2["status"] == "failed" and rec2["failure_stage"] == "test" and rec2["llm_calls"] == 2


def test_leaky_feature_fails(lab_factory):
    rec = run_one(lab_factory(), new_feature_spec("leaky", "MOCK_LEAK"))
    assert rec["status"] == "failed" and "leakage" in rec["failure_reason"].lower()


def test_cheating_feature_rejected(lab_factory):
    rec = run_one(lab_factory(), new_feature_spec("sneaky", "MOCK_CHEAT"))
    assert rec["status"] == "rejected" and rec["failure_stage"] == "guard"


def test_worker_crash_is_contained(lab_factory):
    lab = lab_factory()
    rec = run_one(lab, new_feature_spec("crashy", "MOCK_CRASH"))
    assert rec["status"] == "failed" and rec["failure_stage"] == "worker_crash"
    # the same worker object can keep going
    rec2 = run_one(lab, new_feature_spec("fine", "variance"))
    assert rec2["status"] == "completed"


def test_experiment_timeout(lab_factory):
    lab = lab_factory(experiment__timeout_s=4)
    rec = run_one(lab, new_feature_spec("slow", "MOCK_SLOW"))
    assert rec["status"] == "failed" and "timeout" in (rec["failure_reason"] or "")


def test_duplicate_configs_skipped(lab_factory):
    lab = lab_factory()
    s = dict(hypothesis="Ridge on baseline features as a reference.", scientific_rationale="Reference model rationale.",
             kind="config", feature_set=list(BASE), hyperparameters={"alpha_grid": [1.0]})
    _, st1 = lab.queue(ExperimentSpec(**s))
    eid2, st2 = lab.queue(ExperimentSpec(**s))
    assert (st1, st2) == ("queued", "duplicate")
    assert lab.db.get_experiment(eid2)["duplicate_of"]


def test_sweeps_are_expanded_without_llm(lab_factory):
    lab = lab_factory()
    planner = Planner(lab, ScriptedPlanner())
    specs = planner.to_specs([{"hypothesis": "Penalty strength matters for this feature set.",
                               "rationale": "Bias-variance tradeoff test.", "category": "exploit",
                               "action": "sweep", "sweep": {"target": "alpha_grid", "values": [0.1, 1, 10, 100]}}],
                             proposer="test")
    assert len(specs) == 4 and all(s.kind == "config" for s in specs)
    assert [s.hyperparameters["alpha_grid"] for s in specs] == [[0.1], [1], [10], [100]]
    assert lab.db.llm_totals()["calls"] == 0


def test_replicates_share_hypothesis_group(lab_factory):
    lab = lab_factory()
    planner = Planner(lab, ScriptedPlanner())
    specs = planner.to_specs([{"hypothesis": "Gene-gene relationships improve prediction.",
                               "rationale": "Regulatory structure.", "category": "explore", "action": "new_feature",
                               "replicates": 3, "new_feature": {"name": "gene_rel", "description": "x"}}], "t")
    assert len(specs) == 3 and len({s.hypothesis_group for s in specs}) == 1
    ids = [lab.queue(s)[0] for s in specs]
    names = {lab.db.get_experiment(i)["new_feature"] for i in ids}
    assert len(names) == 3  # independent implementations get distinct feature names


def test_controller_end_to_end_and_reproduce(lab_factory):
    lab = lab_factory()
    ctl = Controller(lab, workers=2, seconds=90, worker_provider=MockProvider(), planner_provider=ScriptedPlanner(),
                     quiet=True)
    t0 = time.time()
    summary = ctl.run()
    assert time.time() - t0 < 90 + 30
    assert summary["best"]["score"] > summary["baseline"]["score"]
    assert summary["experiments_completed"] >= 5
    assert summary["generalization_query_only"], "query-only evaluation should run at the end"
    assert len(lab.oracle.queries) <= lab.oracle.max_queries
    assert (lab.run_dir / "summary.json").exists() and (lab.run_dir / "summary.md").exists()
    # lineage reaches back to a baseline
    assert summary["lineage"][0]["added"] == "baseline"
    import reproduce
    r = reproduce.reproduce(lab, summary["best"]["experiment_id"])
    assert r["reproducible"], r


def test_deadline_is_enforced(lab_factory):
    lab = lab_factory(experiment__timeout_s=120, run__shutdown_grace_s=2)
    # every hypothesis is pathologically slow; the controller must still stop on time
    class SlowPlanner(ScriptedPlanner):
        def propose(self, research_state, n, mix, max_tokens):
            from genemila.providers.base import LLMResponse
            hyps = [{"hypothesis": f"Slow idea number {self.cursor + i} is worth testing.", "rationale": "Tests deadline handling.",
                     "category": "explore", "action": "new_feature",
                     "new_feature": {"name": f"slow{self.cursor + i}", "description": "MOCK_SLOW"}} for i in range(n)]
            self.cursor += n
            return LLMResponse(json.dumps({"hypotheses": hyps}))

    class FastSmokeMock(MockProvider):
        pass

    ctl = Controller(lab, workers=2, seconds=12, worker_provider=FastSmokeMock(), planner_provider=SlowPlanner(),
                     quiet=True)
    lab.cfg["experiment"]["timeout_s"] = 120
    t0 = time.time()
    ctl.run()
    elapsed = time.time() - t0
    assert elapsed < 12 + 2 + 10 + 15, elapsed
    statuses = lab.db.count_by_status()
    assert not any(k in statuses for k in ("claimed", "implementing", "testing", "running"))
    assert statuses.get("killed", 0) >= 1
    assert (lab.run_dir / "summary.json").exists()


def test_planning_scales_with_workers_and_state_is_bounded(lab_factory):
    from genemila.controller import Controller
    from genemila.research_state import SECTION_CHARS, render_state
    lab = lab_factory()
    c = Controller(lab, workers=16, seconds=1800, worker_provider=MockProvider(), planner_provider=ScriptedPlanner())
    assert c.planner_concurrency == 3 and c.planner_batch == 12
    assert lab.gateway.role_caps["planner"] == 7.5  # $15/h for a 30-minute run
    assert Controller(lab, workers=4, seconds=60, worker_provider=MockProvider(),
                      planner_provider=ScriptedPlanner()).planner_concurrency == 1
    state = {"in_flight": [f"hypothesis {i} " + "x" * 80 for i in range(500)], "best": {"score": 0.5}}
    text = render_state(state)
    assert "## BEST" in text and len(text) < 2 * SECTION_CHARS  # a long section cannot push others out


def test_truncated_reasoning_is_not_retried(lab_factory):
    """A reasoning model that spends the whole output limit before writing code fails once, cleanly;
    the same provider is not asked again (it would be truncated the same way), escalation still runs."""
    lab = lab_factory()
    prov = MockProvider()
    rec = run_one(lab, new_feature_spec("thinker", "MOCK_TRUNCATE variance"), provider=prov)
    assert rec["status"] == "failed" and rec["failure_stage"] == "llm_truncated", rec
    assert prov.calls == 1 and rec["llm_calls"] == 1
    assert "output limit" in rec["failure_reason"]

    class Fixer(MockProvider):
        def diagnose(self, task, code, error, max_tokens):
            nf = dict(task["new_feature"], description="variance", implementation_hint="variance")
            return super().diagnose(dict(task, new_feature=nf), code, error, max_tokens)

    rec2 = run_one(lab, new_feature_spec("thinker2", "MOCK_TRUNCATE variance"), escalation=Fixer(model="big"))
    assert rec2["status"] == "completed", rec2["failure_reason"]
