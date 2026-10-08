import json

from genemila.research_state import build_state, render_state


def test_prior_campaign_memory_excludes_held_out_results(lab_factory):
    """Continuations may learn visible results, never the previous sealed score."""
    lab = lab_factory()
    prior = {
        "run_id": "previous_campaign",
        "best_visible": 0.61,
        "best_sealed": 0.987654321,
        "model": "ridge",
        "features": ["control_mean", "useful_transfer"],
        "helpful_features": ["useful_transfer"],
        "unhelpful_features": ["unhelpful_transform"],
        "failed_ideas": [{"idea": "constant feature", "stage": "validate"}],
    }
    (lab.run_dir / "warm_start.json").write_text(json.dumps(prior))
    state = build_state(lab)
    memory = state["prior_campaign"]
    assert memory["its_best"] == {
        "visible": 0.61,
        "model": "ridge",
        "features": ["control_mean", "useful_transfer"],
    }
    assert memory["features_that_helped_there"] == ["useful_transfer"]
    assert memory["features_that_did_not_help_there"] == ["unhelpful_transform"]
    assert memory["ideas_that_failed_there"] == ["constant feature [validate]"]
    assert str(prior["best_sealed"]) not in render_state(state)
