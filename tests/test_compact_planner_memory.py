"""No providers or biological labels: compact policy and failure-memory plumbing."""

import copy
import json
from types import SimpleNamespace

from genemila.config import load_config
from genemila.feature_memory import read_feature_memory
from genemila.planner import Planner


def test_planner_children_and_sweeps_preserve_compact_parent():
    cfg = load_config(overrides={"curation": {"enabled": True}})
    selector = {"method": "lasso", "alpha": .001}
    raw = {"experiment_id": "raw", "feature_set_json": ["a", "b", "c"],
           "status": "completed", "model_type": "ridge"}
    compact = {"experiment_id": "compact", "feature_set_json": ["a", "b"],
               "status": "completed", "model_type": "ridge", "seed": 37,
               "hyperparameters_json": {"alpha_grid": [1.], "column_selection": selector,
                                        "cv_folds": 5, "cv_seed": 0}}
    lab = SimpleNamespace(cfg=cfg, best=lambda: compact, known_features=lambda: {"a", "b", "c"},
                          db=SimpleNamespace(query=lambda *args: [raw], get_experiment=lambda eid: None))
    planner = Planner(lab, SimpleNamespace(name="scripted", model="scripted"))
    planner._priorities = lambda: {}
    hypotheses = [{"hypothesis": "Check a simpler candidate configuration",
                   "rationale": "Remove redundant signal without extra generation",
                   "action": "ablate", "remove_features": ["b"]},
                  {"hypothesis": "Refine the selected compact model penalty",
                   "rationale": "Changing the penalty should preserve column screening",
                   "action": "sweep", "sweep": {"target": "alpha_grid", "values": [[.1], [10.]]}}]
    before = copy.deepcopy(compact)
    specs = planner.to_specs(hypotheses, proposer="fixture", rnd=1)
    assert len(specs) == 3
    assert all(s.parent_experiment_id == "compact" for s in specs)
    assert all(s.seed == 37 for s in specs)
    assert all(s.hyperparameters["column_selection"] == selector for s in specs)
    assert all("cv_seed" not in s.hyperparameters for s in specs)
    assert specs[0].feature_set == ["a"]
    assert compact == before


def test_repeated_failures_do_not_erase_older_distinct_lessons(tmp_path):
    path = tmp_path / "board.json"
    old = {"status": "failed", "candidate_signature": "old", "reason": "constant feature",
           "feature_names": ["old_feature"]}
    repeated = {"status": "failed", "candidate_signature": "repeated", "reason": "selector convergence",
                "feature_names": ["new_feature"]}
    path.write_text(json.dumps({"archive": [old] + [repeated] * 30}))
    memory = read_feature_memory(path, max_recent=2)
    assert [r["candidate_signature"] for r in memory["recent_archive"]] == ["old", "repeated"]
    assert memory["archive_window"]["records_examined"] == 31
    assert memory["archive_window"]["failure_classes"] == {"constant": 1, "convergence": 30}


def test_failure_summary_cannot_surface_nonvisible_scores(tmp_path):
    path = tmp_path / "board.json"
    path.write_text(json.dumps({"archive": [{"status": "failed", "candidate_signature": "one",
        "reason": "held-out score 0.99991 regressed", "feature_names": ["x"]}]}))
    memory = read_feature_memory(path)
    assert memory["archive_window"]["failure_classes"] == {"other": 1}
    assert "0.99991" not in json.dumps(memory)
