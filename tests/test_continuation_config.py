"""Config wiring only: no datasets, agents, evaluations, or controller workers."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from genemila.config import load_config
from genemila.controller import Controller
from run_research import build_config, parse_args


def test_strict_continuation_and_shared_board_are_opt_in_cli_settings():
    defaults = load_config()
    assert defaults["run"]["warm_start_strict"] is False
    assert defaults["feature_board"]["path"] == ""
    configured = build_config(parse_args([
        "--set", "run.warm_start_strict=true", "--set", "feature_board.path=/example/board.sqlite",
    ]))
    assert configured["run"]["warm_start_strict"] is True
    assert configured["feature_board"]["path"] == "/example/board.sqlite"


@pytest.mark.parametrize("strict", [None, False, True])
def test_controller_forwards_strict_policy_before_starting_workers(monkeypatch, strict):
    import genemila.controller as controller_module

    class StopBeforeWorkers(Exception):
        pass

    observed = []

    def warm_start(path, *, strict=False):
        observed.append((path, strict))
        raise StopBeforeWorkers

    monkeypatch.setattr(controller_module, "_raise_fd_limit", lambda: None)
    ctl = Controller.__new__(Controller)
    ctl.cfg = {"run": {"continue_from": "/example/previous"}}
    if strict is not None:
        ctl.cfg["run"]["warm_start_strict"] = strict
    ctl.seconds, ctl.n_workers, ctl.n_cpu = 0, 0, 0
    ctl._log = lambda *args: None
    ctl.lab = SimpleNamespace(
        db=SimpleNamespace(execute=lambda *args: None), run_id="fixture", dataset="fixture", split_id="fixture",
        git_head_dirty=lambda: False, gateway=SimpleNamespace(role_caps={"worker": 0., "planner": 0.}),
        record_analytic_baselines=lambda: None, queue_model_baselines=lambda: None, warm_start=warm_start,
    )
    with pytest.raises(StopBeforeWorkers):
        ctl.run()
    assert observed == [(Path("/example/previous"), strict is True)]
