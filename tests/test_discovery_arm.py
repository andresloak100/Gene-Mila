"""A run in discovery mode (schedule.discovery, docs/DISCOVERY_MODE.md) is its own arm in every table (#72): the
label gets the suffix " (discovery)" for the LLM arms and the scripted control alike, so lab_table and the tools that
group by run_arm never pool it with the clean runs of the same planner and workers."""

from genemila.benchmark.table import run_arm


def _with_discovery(cfg: dict, value) -> dict:
    return {**cfg, "schedule": {**(cfg.get("schedule") or {}), "discovery": value}}


def test_run_arm_labels_a_discovery_run_as_its_own_arm():
    llm = {"planner": {"provider": "deepseek", "model": "deepseek-v4-pro"},
           "worker": {"provider": "deepseek", "model": "deepseek-flash"}, "run": {}, "schedule": {"python_exploit": True}}
    plain = "deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers"
    assert run_arm(llm) == plain
    assert run_arm(_with_discovery(llm, False)) == plain  # the default, off, changes nothing
    assert run_arm(_with_discovery(llm, True)) == plain + " (discovery)"
    ctl = {"planner": {"provider": "scripted"}, "worker": {"provider": "mock"}, "run": {}}
    assert run_arm(_with_discovery(ctl, True)) == "scripted control (no LLM) (discovery)"
    assert run_arm(ctl) == "scripted control (no LLM)"


def test_discovery_suffix_composes_with_the_other_arm_markers():
    cfg = {"planner": {"provider": "deepseek", "model": "deepseek-v4-pro"},
           "worker": {"provider": "deepseek", "model": "deepseek-flash"},
           "run": {"external_knowledge": ["replogle2022_k562"]}, "schedule": {"python_exploit": False, "discovery": True}}
    assert run_arm(cfg) == ("deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash workers (no exploit) "
                            "(external knowledge: replogle2022_k562) (discovery)")
    # a planner that changed during the run stays its own arm, and the discovery suffix rides along
    summary = {"planner": {"mixed": True, "configured": "claude_cli:opus", "used": ["claude_cli:opus", "deepseek:deepseek-v4-pro"]}}
    cfg2 = {"planner": {"provider": "claude_cli", "model": "opus"},
            "worker": {"provider": "deepseek", "model": "deepseek-flash"}, "run": {}, "schedule": {"discovery": True}}
    assert run_arm(cfg2, summary) == ("claude_cli:opus -> deepseek:deepseek-v4-pro planner, deepseek:deepseek-flash "
                                      "workers (discovery)")
    # a config without a schedule section at all (older run directories) is unchanged
    assert run_arm({"planner": {"provider": "scripted"}, "worker": {"provider": "mock"}}) == "scripted control (no LLM)"
