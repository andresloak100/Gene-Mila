"""Sealed feedback must not follow a campaign into its next planner request."""

import json

import pytest

from genemila.planner import Planner
from genemila.providers.base import AgentProvider, LLMResponse


VISIBLE_SCORE = 0.8123456789
SEALED_SCORE = 0.123456789876543
FEATURES = ["control_mean", "mean_response", "is_target"]


class CapturingPlanner(AgentProvider):
    """Exercise the real prompt builder with a local, unmetered provider."""

    name = "scripted"

    def __init__(self):
        super().__init__("capture")
        self.requests = []

    def complete(self, system, user, max_tokens):
        self.requests.append(user)
        return LLMResponse(text='{"hypotheses": []}', provider=self.name, model=self.model)


def _continued_lab(lab_factory):
    previous = lab_factory()
    for eid, visible, sealed in (("EXP_0900", VISIBLE_SCORE, SEALED_SCORE),
                                 ("EXP_0901", 0.4, 0.99)):
        previous.db.insert_experiment({
            "experiment_id": eid, "run_id": previous.run_id, "status": "completed", "kind": "config",
            "category": "exploit", "hypothesis": "Synthetic visible-selected model",
            "feature_set_json": FEATURES, "feature_params_json": {}, "model_type": "ridge",
            "hyperparameters_json": {"alpha": 10.0}, "best_alpha": 10.0,
            "primary_score": visible, "query_metrics_json": {"primary": sealed},
            "finished_at": 1.0, "dataset": previous.dataset, "split_id": previous.split_id,
        })
    continued = lab_factory(run__continue_from=str(previous.run_dir))
    info = continued.warm_start(previous.run_dir)
    return previous, continued, info


def test_new_warm_start_metadata_keeps_visible_selection_without_sealed_feedback(lab_factory):
    previous, continued, info = _continued_lab(lab_factory)
    stored = json.loads((continued.run_dir / "warm_start.json").read_text())
    assert stored == info
    assert "best_sealed" not in info
    assert str(SEALED_SCORE) not in json.dumps(info)
    assert info["best_experiment"] == "EXP_0900"  # The lower sealed score cannot change the selection.
    assert info["best_visible"] == VISIBLE_SCORE
    assert info["model"] == "ridge" and info["features"] == FEATURES
    queued = continued.db.get_experiment(info["start_experiment"])
    assert queued["feature_set_json"] == FEATURES
    assert queued["hyperparameters_json"]["alpha"] == 10.0
    # Historical results remain available for reporting and are never rewritten by this fix.
    assert previous.db.get_experiment("EXP_0900")["query_metrics_json"] == {"primary": SEALED_SCORE}


@pytest.mark.parametrize("legacy_metadata", [False, True], ids=["new", "legacy"])
def test_actual_planner_prompt_excludes_sealed_feedback(lab_factory, legacy_metadata):
    previous, continued, info = _continued_lab(lab_factory)
    warm = continued.run_dir / "warm_start.json"
    if legacy_metadata:
        info["best_sealed"] = SEALED_SCORE
        warm.write_text(json.dumps(info))
    before = warm.read_bytes()
    provider = CapturingPlanner()
    assert Planner(continued, provider).refill(1) == []
    assert len(provider.requests) == 1
    request = provider.requests[0]
    recorded = (continued.run_dir / "planner" / "state_001.txt").read_text()
    for text in (request, recorded):
        assert str(SEALED_SCORE) not in text
        assert '"sealed"' not in text and '"best_sealed"' not in text
        assert f'"visible":{VISIBLE_SCORE}' in text
        assert '"model":"ridge"' in text
        assert previous.run_id in text and "mean_response" in text
        assert "PRIOR CAMPAIGN" in text
    assert warm.read_bytes() == before  # Legacy metadata is filtered at the boundary, not modified on disk.
