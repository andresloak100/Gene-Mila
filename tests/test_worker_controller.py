import json
import threading
import time

import pytest

from genemila.controller import Controller
from genemila.planner import Planner
from genemila.providers.base import ProviderError
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
    assert lab.gateway.role_caps["planner"] == 32.0  # $4 per worker-hour x 16 workers x 0.5 h
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


def test_transient_api_error_is_requeued_once(lab_factory):
    """A retryable provider error (429/5xx/network) puts the experiment back in the queue for another attempt
    instead of recording a failed hypothesis; the second attempt completes."""
    lab = lab_factory()
    prov = MockProvider()
    eid, status = lab.queue(new_feature_spec("flaky", "MOCK_API_ERROR variance"))
    w = Worker(lab, "W0", prov, None, threading.Semaphore(2))
    w.process(lab.db.claim_next("W0"))
    rec = lab.db.get_experiment(eid)
    assert rec["status"] == "queued" and rec["worker_id"] is None and "requeued" in rec["failure_reason"]
    w.process(lab.db.claim_next("W0"))
    rec = lab.db.get_experiment(eid)
    assert rec["status"] == "completed", rec["failure_reason"]
    assert rec["attempts"] == 2
    # a hopeless retryable error gives up at max_attempts
    lab2 = lab_factory()

    class Down(MockProvider):
        def implement(self, task, max_tokens):
            raise ProviderError("simulated HTTP 503", retryable=True)

    eid2, _ = lab2.queue(new_feature_spec("down", "variance"))
    w2 = Worker(lab2, "W0", Down(), None, threading.Semaphore(2))
    w2.process(lab2.db.claim_next("W0"))
    assert lab2.db.get_experiment(eid2)["status"] == "queued"
    w2.process(lab2.db.claim_next("W0"))
    rec2 = lab2.db.get_experiment(eid2)
    assert rec2["status"] == "failed" and rec2["failure_stage"] == "llm_api"


def test_python_exploit_fills_the_queue_without_llm(lab_factory):
    """With the planner limited to one round, the deterministic exploit engine keeps proposing follow-ups
    around the best model; each configuration runs at most once and nothing is re-proposed."""
    from genemila import exploit
    lab = lab_factory(schedule__max_planner_calls=1)
    ctl = Controller(lab, workers=2, seconds=60, worker_provider=MockProvider(), planner_provider=ScriptedPlanner(),
                     quiet=True)
    summary = ctl.run()
    rows = lab.db.query("SELECT * FROM experiments WHERE proposer='python:exploit'")
    assert rows, "exploit experiments should have been queued once the planner stopped"
    assert all(r["kind"] == "config" and r["category"] == "exploit" and r["parent_id"] for r in rows)
    assert all(r["status"] != "duplicate" for r in rows), "exploit never re-proposes a tried configuration"
    assert len({r["config_hash"] for r in rows}) == len(rows)
    groups = [r["hypothesis_group"] for r in rows]
    assert any(g.startswith("exploit_alpha_") for g in groups) or any(g.startswith("exploit_model_") for g in groups)
    assert summary["experiments_completed"] >= 4
    # once everything around the best has been tried, propose() is empty rather than looping
    best = lab.best()
    for spec in exploit.candidates(lab, best):
        lab.queue(spec)
    assert exploit.propose(lab, 5) == []


def test_warm_start_continues_a_campaign(lab_factory, tmp_path, dataset):
    """A second run on the same split imports the first run's useful features, starts from its best model and
    tells the planner what was already learned; a run on another split is refused."""
    first = lab_factory(schedule__max_planner_calls=2)
    Controller(first, workers=2, seconds=45, worker_provider=MockProvider(), planner_provider=ScriptedPlanner(),
               quiet=True).run()
    best = first.best()
    assert best["kind"] == "new_feature" or best["feature_set_json"]
    second = lab_factory(run__continue_from=str(first.run_dir), schedule__max_planner_calls=1)
    ctl = Controller(second, workers=2, seconds=30, worker_provider=MockProvider(), planner_provider=ScriptedPlanner(),
                     quiet=True)
    summary = ctl.run()
    info = json.loads((second.run_dir / "warm_start.json").read_text())
    assert info["run_id"] == first.run_id and info["features"] == best["feature_set_json"]
    imported = [f for f in second.db.features() if (f.get("creator_experiment") or "").startswith("warm:")]
    assert {f["name"] for f in imported} >= {f for f in best["feature_set_json"] if f not in ("control_mean", "mean_response", "is_target")}
    assert all((second.store / f"{f['name']}.py").exists() for f in imported)
    start = second.db.query("SELECT * FROM experiments WHERE proposer='python:warm_start'")
    assert len(start) == 1 and start[0]["status"] == "completed", start[0].get("failure_reason")
    assert start[0]["feature_set_json"] == best["feature_set_json"]
    assert abs(start[0]["primary_score"] - best["primary_score"]) < 1e-6  # same model, same split: same score
    assert summary["continued_from"] == str(first.run_dir)
    from genemila.research_state import build_state, render_state
    text = render_state(build_state(second))
    assert "PRIOR CAMPAIGN" in text and first.run_id in text
    # another split: refused
    from genemila.data.synthetic import generate
    other = generate(tmp_path / "other", n_genes=120, n_perts=30, n_control=600, cells_per_pert=40, seed=1, split_seed=7)
    from genemila.lab import Lab
    from conftest import make_cfg
    cfg = make_cfg(tmp_path, run__continue_from=str(first.run_dir))
    cfg["run"]["data_dir"] = str(other)
    lab3 = Lab(cfg, tmp_path / "run_other", other, repo=second.repo)
    try:
        with pytest.raises(RuntimeError, match="cannot continue"):
            lab3.warm_start(first.run_dir)
    finally:
        lab3.stop_event.set(); lab3.kill_event.set(); lab3.close()
