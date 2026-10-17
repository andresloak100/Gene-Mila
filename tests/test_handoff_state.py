"""Operational handoff evidence is tested with synthetic files, never lab runs or data."""

import json
import sys
from pathlib import Path

import pytest

import handoff_state as hs


def make_run(root, name, planner=None):
    run = root / name
    run.mkdir(parents=True)
    (run / "config.json").write_text(json.dumps({
        "run": {"workers": 4, "seed": 1, "dataset": "synthetic"},
        "planner": {"provider": "deepseek", "model": "test"},
        "worker": {"provider": "mock"},
    }))
    (run / "summary.json").write_text(json.dumps({
        "base_commit": "abc123456", "duration_s": 1200, "experiments_completed": 3,
        "best": {"score": 0.6}, "planner": planner or {"mixed": False},
        "generalization_query_only": [{"kind": "config", "query_only_score": 0.5}],
    }))
    return run


def read_run(run, logs):
    evidence, incomplete, warnings = hs.stop_evidence(logs, {run.name})
    return hs.run_state(run, evidence=evidence.get(run.name),
                        evidence_incomplete=run.name in incomplete), warnings


def test_summary_does_not_erase_stop_evidence_or_echo_marker_contents(tmp_path, monkeypatch):
    run = make_run(tmp_path, "norman_ds_addstart_w4_r1")
    original = hs.run_state(run)
    logs = tmp_path / "logs"
    logs.mkdir()
    marker = logs / "block_after_n4_stopped_r1.txt"
    marker.write_text(f"2026-10-11T22:38Z {run.name}: exit code 247; killed or interrupted; "
                      "PRIVATE_MARKER_CONTENT\n")
    (logs / f"{run.name}.passed").touch()  # a pass marker cannot cancel explicit stop evidence
    (logs / f"{run.name}.log").write_text("must never be opened")
    real_open = Path.open

    def guarded_open(path, *args, **kwargs):
        assert path.suffix != ".log", "the handoff reader must not open full run logs"
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    result, warnings = read_run(run, logs)
    assert result["state"] == ("stopped (killed or interrupted; summary exists; "
                               "evidence: block_after_n4_stopped_r1.txt)")
    assert not warnings
    assert "PRIVATE_MARKER_CONTENT" not in json.dumps(result)
    assert "watchdog" not in result["state"].lower()
    assert {k: v for k, v in result.items() if k not in ("state", "stop_evidence")} == {
        k: v for k, v in original.items() if k != "state"}


def test_stop_records_match_complete_names_with_or_without_timestamp(tmp_path):
    runs = [make_run(tmp_path, name) for name in ("run_r1", "run_r10", "other")]
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "block_stopped.txt").write_text(
        "2026-10-11T22:38:00Z run_r10: killed or interrupted;\n"
        "run_r1: cost $3.00 by the ledger, over $2.00;\n"
        "prefix other: killed or interrupted;\n")
    evidence, incomplete, warnings = hs.stop_evidence(logs, {r.name for r in runs})
    assert evidence["run_r1"][0]["reason"] == "block stop recorded"
    assert evidence["run_r10"][0]["reason"] == "killed or interrupted"
    assert "other" not in evidence
    assert not incomplete and not warnings
    result = hs.run_state(runs[0], evidence=evidence["run_r1"])
    assert result["state"].startswith("stopped (block stop recorded; summary exists;")
    assert "killed" not in result["state"]
    assert hs.run_state(runs[2])["state"] == "finished"


def test_backstop_requires_matching_run_and_explicit_termination(tmp_path):
    run = make_run(tmp_path, "run_r1")
    logs = tmp_path / "logs"
    logs.mkdir()
    marker = logs / "run_r1.backstop.txt"
    marker.write_text("2026-10-11T23:38Z run_r1: still running 5400 s; terminated (pid 123)\n")
    result, warnings = read_run(run, logs)
    assert "stopped (backstop termination recorded; summary exists;" in result["state"]
    assert "run_r1.backstop.txt" in result["state"]
    assert not warnings
    for content in ("run_r10: terminated\n", "run_r1: waiting\n"):
        marker.write_text(content)
        result, warnings = read_run(run, logs)
        assert result["state"].startswith("status unverified (stop evidence unavailable;")
        assert warnings and "run_r1.backstop.txt" in warnings[0]


@pytest.mark.parametrize("suffix", ["contaminated", "interrupted"])
def test_stop_preserves_exclusion_and_planner_history(tmp_path, suffix):
    run = make_run(tmp_path, f"run_{suffix}", {"mixed": True, "used": ["deepseek:test", "scripted"]})
    original = hs.run_state(run)
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "block_stopped.txt").write_text(f"{run.name}: killed or interrupted;\n")
    result, warnings = read_run(run, logs)
    assert result["state"].startswith(f"excluded ({suffix}); stopped (")
    assert "planner changed mid-run: deepseek:test -> scripted" in result["state"]
    assert result["arm"] == original["arm"]
    assert result["best_sealed"] == original["best_sealed"]
    assert not warnings


@pytest.mark.parametrize("marker_name", ["block_stopped.txt", "run_r1.backstop.txt"])
def test_unreadable_evidence_warns_without_exposing_contents(tmp_path, monkeypatch, marker_name):
    run = make_run(tmp_path, "run_r1")
    logs = tmp_path / "logs"
    logs.mkdir()
    marker = logs / marker_name
    marker.touch()
    real_open = Path.open

    def unreadable(path, *args, **kwargs):
        if path == marker:
            raise PermissionError("PRIVATE_EXCEPTION_TEXT")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", unreadable)
    result, warnings = read_run(run, logs)
    assert result["state"] == "status unverified (stop evidence unavailable; summary exists)"
    assert marker_name in warnings[0]
    assert "PRIVATE_EXCEPTION_TEXT" not in json.dumps([result, warnings])


def test_no_logs_or_no_matching_record_leaves_run_unchanged(tmp_path):
    run = make_run(tmp_path, "run_r1")
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "block_stopped.txt").write_text("run_r10: killed or interrupted;\n")
    for location in (None, logs):
        result, warnings = read_run(run, location)
        assert result == hs.run_state(run)
        assert not warnings


def test_unreadable_log_directory_does_not_certify_run_finished(tmp_path):
    run = make_run(tmp_path, "run_r1")
    result, warnings = read_run(run, tmp_path / "missing_logs")
    assert result["state"].startswith("status unverified")
    assert warnings


def test_cli_displays_latest_state_and_retains_json_head(tmp_path, monkeypatch, capsys):
    runs = tmp_path / "runs"
    run = make_run(runs, "run_r1")
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "block_stopped.txt").write_text(f"{run.name}: killed or interrupted;\n")
    lines = ["Old entry"] + [f"historical line {i}" for i in range(80)] + ["Latest entry: STOP remains"]
    (logs / "STATE.md").write_text("\n".join(lines))
    monkeypatch.setattr(hs, "processes", lambda: [])
    monkeypatch.setattr(hs, "git_state", lambda *args, **kwargs: {
        "branch": "test", "head": "abc1234", "dirty_files": 0, "last_commit": "synthetic",
        "integration_branch": hs.INTEGRATION_BRANCH, "integration_head": "abc1234",
        "integration_fetched": "synthetic", "ahead": 0, "behind": 0, "fetched_now": False,
    })
    args = ["handoff_state.py", "--runs", str(runs), "--logs", str(logs)]
    monkeypatch.setattr(sys, "argv", args + ["--json"])
    hs.main()
    state = json.loads(capsys.readouterr().out)
    assert state["state_head"] == lines[:40]
    assert state["state_tail"] == lines[-40:]
    assert state["runs"][0]["state"].startswith("stopped (killed or interrupted;")
    monkeypatch.setattr(sys, "argv", args)
    hs.main()
    text = capsys.readouterr().out
    assert "Latest appended state notes" in text and "last 40 lines" in text
    assert "Latest entry: STOP remains" in text and "Old entry" not in text
    assert "stopped (killed or interrupted; summary exists; evidence: block_stopped.txt)" in text
