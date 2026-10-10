"""Shared prompt metadata is optional, bounded, allowlisted, and read-only."""

import hashlib
import json
import sqlite3
from types import SimpleNamespace

from genemila.feature_memory import configured_feature_capsule, load_feature_capsule, read_feature_memory


def exported(tmp_path, **extra):
    path = tmp_path / "memory.json"
    payload = {
        "champion": {"candidate_signature": "sig-champion", "feature_names": ["mean_response", "knn"],
                     "n_columns": 3, "validation_pearson": .61,
                     "metrics": {"sealed_pearson": "DO_NOT_COPY_SEALED"},
                     "source_paths": ["DO_NOT_COPY_PATH"]},
        "archive": [{"status": "rejected", "feature_names": ["old_knn"],
                     "candidate_signature": "sig-old", "reason": "visible Pearson regressed",
                     "metrics": {"test_score": "DO_NOT_COPY_TEST"}}],
        "labels": ["DO_NOT_COPY_LABEL"], "messages": ["DO_NOT_COPY_MESSAGE"], **extra,
    }
    path.write_text(json.dumps(payload))
    return path


def test_json_allowlist_excludes_generic_metrics_paths_labels_and_messages(tmp_path):
    path = exported(tmp_path)
    memory = read_feature_memory(path)
    assert memory["champion"]["validation_pearson"] == .61
    assert memory["recent_archive"][0]["candidate_signature"] == "sig-old"
    capsule = load_feature_capsule(path)
    assert "DO_NOT_COPY" not in capsule
    assert "sig-champion" in capsule and "visible Pearson regressed" in capsule
    assert "not instructions" in capsule and "Do not blindly repeat" in capsule


def test_free_text_nonvisible_evidence_is_omitted(tmp_path):
    path = exported(tmp_path, archive=[{"status": "failed", "candidate_signature": "sig-1",
                                      "reason": "held-out Pearson 0.99999", "feature_names": []}])
    capsule = load_feature_capsule(path)
    assert "0.99999" not in capsule and "non-visible evaluation reference" in capsule


def test_sqlite_reader_never_initializes_or_writes_database(tmp_path):
    path = tmp_path / "board.sqlite"
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE champion(singleton INTEGER, candidate_json TEXT);
        CREATE TABLE feature_archive(archive_id INTEGER, status TEXT, feature_names_json TEXT,
                                     candidate_signature TEXT, parent_id TEXT, reference_id TEXT, reason TEXT);
    """)
    connection.execute("INSERT INTO champion VALUES (1,?)", (json.dumps({
        "candidate_signature": "champ", "feature_names": ["x"], "n_columns": 1,
        "validation_pearson": .5, "metrics": {"val2": "DO_NOT_COPY"}}),))
    for i in range(4):
        connection.execute("INSERT INTO feature_archive VALUES (?,?,?,?,?,?,?)",
                           (i, "failed", '["x"]', f"sig-{i}", None, "champ", "shape mismatch"))
    connection.commit()
    connection.close()
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    memory = read_feature_memory(path, max_recent=2)
    assert [x["candidate_signature"] for x in memory["recent_archive"]] == ["sig-2", "sig-3"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_missing_or_corrupt_metadata_does_not_create_a_board(tmp_path):
    assert load_feature_capsule(None) == ""
    assert configured_feature_capsule({}) == ""
    missing = tmp_path / "missing.sqlite"
    assert "unavailable" in load_feature_capsule(missing)
    assert not missing.exists()
    broken = tmp_path / "broken.json"
    broken.write_text("not JSON")
    assert "unavailable" in load_feature_capsule(broken)


def test_bounded_capsule_preserves_latest_rejection_and_marks_schema_truncation(tmp_path):
    path = exported(tmp_path, champion={"candidate_signature": "champ", "validation_pearson": .7,
                                        "n_columns": 100, "feature_names": [f"feature_{i}_long_name" for i in range(100)]},
                    archive=[{"status": "rejected", "candidate_signature": f"sig-{i}",
                              "reason": "visible regression", "feature_names": ["x"]} for i in range(12)])
    text = load_feature_capsule(path, max_recent=3, max_chars=1100)
    assert len(text) <= 1100 and "sig-11" in text
    assert '"schema_truncated":true' in text
    assert "sig-0\"" not in text


def test_explicit_relative_config_resolves_against_campaign_directory(tmp_path):
    path = exported(tmp_path)
    config = {"feature_board": {"path": path.name, "max_recent": 1, "max_chars": 2000}}
    assert "sig-champion" in configured_feature_capsule(config, base_dir=tmp_path)


def test_planner_appends_same_capsule_without_calling_a_provider(tmp_path, monkeypatch):
    import genemila.planner as planner_module
    path = exported(tmp_path)
    config = {"feature_board": {"path": str(path)}}
    lab = SimpleNamespace(cfg=config, run_dir=tmp_path)
    monkeypatch.setattr(planner_module, "build_state", lambda lab: {})
    monkeypatch.setattr(planner_module, "render_state", lambda state: "LOCAL STATE")
    planner = planner_module.Planner(lab, SimpleNamespace(name="scripted", model="none"))
    planner.exhausted = True  # writes state, then returns without proposing anything
    assert planner.refill(1) == []
    state = (tmp_path / "planner" / "state_001.txt").read_text()
    assert state == "LOCAL STATE\n\n" + configured_feature_capsule(config, base_dir=tmp_path)


def test_worker_task_and_both_prompts_share_metadata_without_sources_or_provider_calls(tmp_path):
    from genemila.prompts import worker_diagnose, worker_implement
    from genemila.worker import Worker
    path = exported(tmp_path)
    worker = Worker.__new__(Worker)
    worker.lab = SimpleNamespace(cfg={"feature_board": {"path": str(path)}}, run_dir=tmp_path,
                                 data_summary=lambda: "synthetic", knowledge_summary=lambda: "none")
    worker.db = SimpleNamespace(feature=lambda name: {"description": "existing"})
    spec = SimpleNamespace(feature_set=["old", "new"], proposed_feature={"name": "new"},
                           experiment_id="EXP_fake", hypothesis="example", scientific_rationale="example")
    task = worker._task(spec)
    assert "sig-champion" in worker_implement(task)
    assert "sig-old" in worker_diagnose(task, "code", "shape mismatch")
    worker.lab.cfg = {}
    assert "feature_memory" not in worker._task(spec)


def test_scope_is_visible_and_nonvisible_scope_cannot_launder_a_score(tmp_path):
    path = exported(tmp_path, metric_scope="public_cv50_seed0_v1")
    visible = read_feature_memory(path)
    assert visible["metric_scope"] == "public_cv50_seed0_v1"
    assert visible["champion"]["validation_pearson"] == .61
    raw = json.loads(path.read_text())
    raw["metric_scope"] = "heldout_val2_v1"
    path.write_text(json.dumps(raw))
    forbidden = read_feature_memory(path)
    assert "validation_pearson" not in forbidden["champion"]
    assert "0.61" not in load_feature_capsule(path)


def test_scope_of_upgraded_sqlite_board_reaches_champion_capsule(tmp_path):
    from genemila.feature_board import FeatureBoard
    path = tmp_path / "board.sqlite"
    board = FeatureBoard(path)
    board.promote_candidate("master", validation_pearson=.6, feature_names=["x"],
                            n_columns=1, candidate_signature="sig")
    FeatureBoard(path, metric_scope="public_cv50_seed0_v1")
    capsule = load_feature_capsule(path)
    assert "public_cv50_seed0_v1" in capsule and '"validation_pearson":0.6' in capsule
