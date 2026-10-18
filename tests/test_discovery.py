"""Discovery mode (genemila/discovery.py, schedule.discovery; docs/DISCOVERY_MODE.md).

Off by default: the frozen prompt and state tests (tests/test_norman_templates.py) hold every default run's state and
planner message byte for byte. These tests turn it on in the synthetic lab and check what it adds: residual evidence
from the training folds only, inputs instead of idea areas, the derivability score, the planner's judgement of each
round and the dry rule.
"""

import json
import re
import time
from pathlib import Path

import numpy as np

from genemila import discovery, prompts
from genemila.config import load_config
from genemila.controller import Controller
from genemila.planner import Planner
from genemila.providers.base import AgentProvider, LLMResponse
from genemila.providers.mock import MockProvider, ScriptedPlanner
from genemila.research_state import build_state, render_state
from test_worker_controller import new_feature_spec, run_one

MIX = {"explore": 0.65, "exploit": 0.25, "risky": 0.10}
ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------------------------------------------- integrity
def test_discovery_reads_no_held_out_tier():
    """The generator's source never names the held-out tiers, the split file or the oracle: every reading it makes
    comes from the public bundle and the best experiment's out-of-fold predictions of the training perturbations."""
    src = (ROOT / "genemila" / "discovery.py").read_text()
    code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    for word in ("val1", "val2", "private", "splits", "oracle", "query_metrics"):
        assert word not in code, word
    assert discovery.DEFAULTS == {"discovery": False, "discovery_dry_rounds": 3, "discovery_derived_r2": 0.8}
    cfg = load_config()
    assert not discovery.enabled(cfg)
    for key, value in discovery.DEFAULTS.items():  # configs/default.toml says what the code defaults to
        assert cfg["schedule"][key] == value, key


class _NoValidationMeans:
    """lab._val1 with its labels withdrawn: a reading that touched them would raise."""

    def __init__(self, real):
        self.perts = real.perts

    @property
    def means(self):
        raise AssertionError("discovery read the visible validation labels")


# ------------------------------------------------------------------------------------------------- inputs and reads
def test_classify_and_feature_reads():
    assert discovery.classify({"perts": {"A": {}}})["kind"] == "screen"
    table = discovery.classify({"description": "x", "columns": ["pLI", "length"], "genes": {"G1": [0.1, 2]}})
    assert table["kind"] == "table" and table["columns"] == ["pLI", "length"]
    assert discovery.classify({"S1": ["G1", "G2"]})["kind"] == "sets"
    assert discovery.classify([["G1", "G2", 1]])["kind"] == "network"
    assert discovery.classify(["G1", "G2"])["kind"] == "list"
    files = {"gene_annotation": table, "gene_sets": discovery.classify({"S1": ["G1"]})}
    assert discovery.input_names(files) == [*discovery.CONTROL_INPUTS, *discovery.LABEL_INPUTS,
                                            *discovery.TARGET_INPUTS, "gene_annotation", "gene_annotation.pLI",
                                            "gene_annotation.length", "gene_sets"]
    src = ('t = ctx.knowledge("gene_annotation")\ncol = t["columns"].index("pLI")\n'
           'for i, p in enumerate(perts):\n    idx = ctx.target_indices(p)\nx = ctx.control_cells.std(axis=0)\n')
    r = discovery.feature_reads(src, files)
    assert r["inputs"] == {"gene_annotation", "gene_annotation.pLI", "target_genes", "control_cells"}
    assert not r["derived"]
    r = discovery.feature_reads('base = ctx.feature("coexpr", perts)\nreturn base ** 2\n', files)
    assert r["inputs"] == set() and r["derived"]
    # a file opened through a variable still counts when its name is a literal anywhere, or when every file is opened
    assert discovery.feature_reads('name = "gene_sets"\nsets = ctx.knowledge(name)\n', files)["inputs"] == {"gene_sets"}
    assert discovery.feature_reads('for b in ctx.available_knowledge():\n    t = ctx.knowledge(b)\n', files)["inputs"] \
        == {"gene_annotation", "gene_sets"}
    unread = {"gene_annotation.pLI", "gene_annotation.length", "gene_sets", "protein_annotation.membrane"}
    assert discovery.judge_plan(
        [{"action": "new_feature", "new_feature": {"name": "pli_g", "new_input": "gene_annotation.pLI"}},
         {"action": "new_feature", "new_feature": {"name": "len_g", "new_input": "length"}},  # a bare column resolves
         {"action": "new_feature", "new_feature": {"name": "sets", "description": "gene_sets membership of g"}},
         {"action": "combine", "hypothesis": "add gene_sets"},
         {"action": "new_feature", "new_feature": {"name": "x", "description": "a product of existing features"}},
         # a column's bare name in prose is a word, not a read: membrane proteins, nuclear genes
         {"action": "new_feature", "hypothesis": "membrane receptor knockdowns move genes of length above the median",
          "new_feature": {"name": "memb", "description": "membrane-bound targets times coexpr"}},
         # composing another feature is derived whatever it names
         {"action": "new_feature", "new_feature": {"name": "pli_x", "new_input": "gene_annotation.pLI",
                                                   "implementation_hint": "ctx.feature('coexpr') * pLI"}}],
        unread) == [["gene_annotation.pLI"], ["gene_annotation.length"], ["gene_sets"], [], [], [], []]


# ------------------------------------------------------------------------------------------------ the planner's view
def test_state_prompt_and_derivability_in_the_synthetic_lab(lab_factory):
    off = lab_factory()
    off.record_analytic_baselines()
    plain = build_state(off)
    assert "unexplored_idea_areas" in plain and discovery.STATE_EVIDENCE not in plain
    assert not prompts.discovery_flag(render_state(plain))
    assert "new_input" not in prompts.planner_user(render_state(plain), 8, MIX)

    lab = lab_factory(schedule__discovery=True)
    lab.record_analytic_baselines()
    val1 = lab._val1  # the worker scores on it; build_state reads its perturbation count only; the evidence nothing
    lab._val1 = _NoValidationMeans(val1)
    state = build_state(lab)
    assert "unexplored_idea_areas" not in state
    assert state[discovery.STATE_EVIDENCE][0].startswith("not available")
    inputs = "\n".join(state[discovery.STATE_INPUTS])
    assert "gene_sets (sets, " in inputs and "prior_network (network, " in inputs and "transcription_factors (list, " in inputs
    assert "control_mean (read by 1)" in inputs and "train_delta (read by 1)" in inputs and "control_cells (unread)" in inputs
    text = render_state(state)
    assert prompts.discovery_flag(text)
    msg = prompts.planner_user(text, 8, MIX)
    assert prompts.DISCOVERY_PLANNER_NOTE in msg and '"new_input":' in msg and '"predicted_sign":' in msg
    assert "## INPUTS UNEXPLORED" in text and discovery.EVIDENCE_HEADING in text
    assert "at or above 0.8 the feature is flagged derived" in text
    assert "derived_r2" not in json.dumps(plain) and "residual" not in json.dumps(plain)  # the default state: no new key

    # one completed model: the evidence appears, from its training folds, and the feature is scored for derivability
    lab._val1 = val1
    rec = run_one(lab, new_feature_spec("module_g", "gene_set module membership of the target"))
    assert rec["status"] == "completed", rec["failure_reason"]
    dv = rec["diagnostics_json"]["derivability"]
    assert dv["n_rows"] > 0 and -1.0 <= dv["r2"] <= 1.0 and len(dv["per_column"]) == 1
    assert json.loads((Path(rec["artifact_dir"]) / "run_spec.json").read_text())["derivability"] == [rec["new_feature"]]
    lab._val1 = _NoValidationMeans(val1)
    state = build_state(lab)
    ev = state[discovery.STATE_EVIDENCE]
    assert ev[0].startswith(f"From the {len(lab._train.perts)} training perturbations out of fold only ({rec['experiment_id']}")
    assert any(l.startswith("worst: ") for l in ev) and any(l.startswith("genes carrying the residual") for l in ev)
    assert any(l.startswith("residual structure: ") for l in ev)
    inputs = "\n".join(state[discovery.STATE_INPUTS])
    assert "gene_sets (sets, " in inputs and "read by 1 plain" in inputs.split("gene_sets (sets, ")[1].split("\n")[0]
    item = next(i for i in state["features_that_help"] + state["features_that_do_not_help"] if i["feature"] == rec["new_feature"])
    assert item["derived_r2"] == round(dv["r2"], 2) and item["derived"] == (dv["r2"] >= 0.8)
    assert "(truncated)" not in "\n".join(state[discovery.STATE_EVIDENCE] + state[discovery.STATE_INPUTS])
    assert ev[1].startswith("residual structure: ") and ev[-1].startswith("worst: ")
    files = sorted((lab.run_dir / "planner").glob("discovery_EXP_*.json"))
    assert len(files) == 1
    saved = json.loads(files[0].read_text())
    assert saved["available"] and saved["labels_read"] == ["training labels (public.npz)"] and saved["cv_folds"] == 5
    assert len(saved["worst"]) == discovery.TOP_PERTS and all(-1 <= w["oof_pearson_delta"] <= 1 for w in saved["worst"])
    assert set(saved["genes"]["correlations"]) == {"control_mean", "control_std"}  # the synthetic bundle has no table
    assert discovery.unread_inputs(lab) >= {"control_cells", "prior_network", "transcription_factors"}
    assert "gene_sets" not in discovery.unread_inputs(lab)
    assert len(render_state(state)) <= 24000
    lab._val1 = val1
    # the worker is told the input, mechanism and sign only when the hypothesis carries them
    task = {"new_feature": {"name": "f", "description": "d", "implementation_hint": "h", "params": {}},
            "data_summary": lab.data_summary(), "knowledge_summary": "", "experiment_id": "EXP_0001",
            "hypothesis": "h", "rationale": "r", "existing_features": "none"}
    plain_msg = prompts.worker_implement(task)
    assert "must read" not in plain_msg and "Mechanism" not in plain_msg
    task["new_feature"].update(new_input="gene_sets", mechanism="module co-regulation", predicted_sign="positive")
    msg = prompts.worker_implement(task)
    assert "must read" in msg and "gene_sets" in msg and "Mechanism it encodes: module co-regulation" in msg
    assert "Predicted sign of its coefficient: positive" in msg
    assert "gene_sets" in prompts.worker_diagnose(task, "code", "err")


def test_full_evidence_renders_inside_its_budget():
    """A full evidence block with long real-bundle names stays under the evidence section's own budget, so the
    structure reading is never the line a cut removes (it is rendered first, the worst perturbations last)."""
    from genemila.research_state import EVIDENCE_SECTION_CHARS
    group = "REACTOME:Nonsense Mediated Decay (NMD) independent of the Exon Junction Complex (EJC)"
    enriched = [{"group": f"{group} {i}", "hit": 12, "size": 180, "p": 3e-4} for i in range(4)]
    worst = [{"pert": f"ZBTB10+ZNF318_{i}", "oof_pearson_delta": 0.1234, "n_targets_measured": 2, "target_change": -0.81,
              "n_gene_sets": 137, "n_partners": 112, "nearest_by_sets": "CEBPB+CEBPE", "nearest_jaccard": 0.42,
              "coexpr_max": 0.77, "coexpr_with": "KLF1+MAP2K6"} for i in range(discovery.TOP_PERTS)]
    ev = {"available": True, "experiment_id": "EXP_0123", "cv_folds": 5, "n_train": 112, "oof_pearson_delta": 0.6012,
          "worst": worst,
          "genes": {"top_n": 250, "share": 0.43, "correlations": {f"gene_annotation.n_tss_within_100kb_{i}": 0.21 - i / 10
                                                                  for i in range(6)},
                    "enriched": enriched, "under_predicted": [f"GENE{i}" for i in range(8)],
                    "over_predicted": [f"GENE{i}" for i in range(8, 16)]},
          "structure": {"share": 0.31, "null_share": 0.12, "low_rank": True, "top_pert_share": 0.7,
                        "genes": [f"LONGGENENAME{i}" for i in range(8)], "perts": [f"ZBTB10+ZNF318_{i}" for i in range(5)],
                        "enriched": enriched[:3]}}
    lines = discovery.render_evidence(ev)
    body = "\n".join(f"- {l}" for l in lines)
    assert len(body) <= EVIDENCE_SECTION_CHARS, len(body)
    assert lines[1].startswith("residual structure: component 1 holds 31%") and lines[-1].startswith("worst: ")
    assert all(len(name) <= discovery.GROUP_CHARS for name in re.findall(r"REACTOME:[^(]*", body))
    text = render_state({discovery.STATE_EVIDENCE: lines})
    assert "(truncated)" not in text


def test_derivability_scores_a_product_as_derived_and_noise_as_new():
    rng = np.random.default_rng(3)
    n_perts, n_genes = 20, 50
    a, b = rng.normal(size=n_perts * n_genes), rng.normal(size=n_perts * n_genes)
    X = np.stack([a, b, a * b, rng.normal(size=n_perts * n_genes), np.ones(n_perts * n_genes)], axis=1)
    product = discovery.derivability(X, [2], [0, 1], n_perts, n_genes, seed=1)
    assert product["r2"] > 0.95 and product["n_basis"] == 1 + 2 + 2 + 1
    noise = discovery.derivability(X, [3], [0, 1], n_perts, n_genes, seed=1)
    assert noise["r2"] < 0.2
    assert discovery.derivability(X, [4], [0, 1], n_perts, n_genes)["r2"] == 1.0  # a constant is the intercept
    assert discovery.derivability(X, [], [0, 1], n_perts, n_genes)["r2"] is None
    both = discovery.derivability(X, [2, 3], [0, 1], n_perts, n_genes, seed=1)  # every new column in one solve
    assert both["per_column"] == [product["r2"], noise["r2"]] and both["r2"] == np.mean(both["per_column"])
    wide = discovery.derivability(np.concatenate([X, rng.normal(size=(n_perts * n_genes, 200))], axis=1), [2],
                                  [0, 1, *range(5, 205)], n_perts, n_genes, seed=1)
    assert wide["n_basis"] == 1 + 2 * 202 and "products" not in wide["basis"]  # a wide parent: no pairwise products


# ------------------------------------------------------------------------------------------------- judgement and dry
class _FixedPlanner(AgentProvider):
    """An LLM planner that answers each round with the next plan of a fixed list."""
    name = "deepseek"

    def __init__(self, plans):
        super().__init__("fixed")
        self.plans, self.calls = plans, 0

    def complete(self, system, user, max_tokens):
        self.calls += 1
        self.last_user = user
        return LLMResponse(text=json.dumps(self.plans[min(self.calls, len(self.plans)) - 1]), provider=self.name,
                           model=self.model)


def _plan(*features):
    return {"synthesis": "s", "hypotheses": [
        {"title": name, "hypothesis": f"{name} explains part of the residual",
         "rationale": "A biologically motivated test fixture rationale.", "category": "explore",
         "action": "new_feature", "new_feature": {"name": name, "description": desc, "implementation_hint": desc,
                                                  "params": {}, **extra}}
        for name, desc, extra in features]}


def test_judgement_dry_rule_and_summary(lab_factory):
    lab = lab_factory(schedule__discovery=True, schedule__discovery_dry_rounds=2)
    lab.record_analytic_baselines()
    plans = [
        _plan(("tf_g", "whether g is a transcription factor", {"new_input": "transcription_factors",
                                                               "mechanism": "TFs buffer", "predicted_sign": "negative"}),
              ("sq_g", "square of control_mean", {})),
        _plan(("sq2_g", "cube of the control mean", {})),
        _plan(("sq3_g", "rank of control_mean", {"new_input": "control_mean"})),   # read already: not new
        _plan(("ppi_g", "prior_network neighbours of the target", {"new_input": "prior_network"})),
    ]
    prov = _FixedPlanner(plans)
    planner = Planner(lab, prov, [])
    ids = planner.refill(2)
    assert len(ids) == 2 and prov.calls == 1 and prompts.DISCOVERY_PLANNER_NOTE in prov.last_user
    recs = {lab.db.get_experiment(i)["new_feature"].rsplit("_e", 1)[0]: lab.db.get_experiment(i) for i in ids}
    assert recs["tf_g"]["proposed_feature_json"]["novel_inputs"] == ["transcription_factors"]
    assert recs["tf_g"]["proposed_feature_json"]["predicted_sign"] == "negative"
    assert recs["tf_g"]["proposed_feature_json"]["mechanism"] == "TFs buffer"
    assert recs["sq_g"]["proposed_feature_json"]["novel_inputs"] == []
    assert planner.novel_dry == 0 and not planner.dry()
    assert planner.refill(1) and planner.novel_dry == 1 and not planner.dry()
    assert planner.refill(1) and planner.novel_dry == 2 and planner.dry() and planner.discovery_dry
    assert planner.refill(1) == [] and prov.calls == 3, "a dry planner is not asked again"
    kinds = [e["kind"] for e in lab.db.query("SELECT kind FROM events ORDER BY id")]
    assert kinds.count("discovery_round") == 3 and kinds.count("discovery_dry") == 1
    rounds = json.loads((lab.run_dir / "planner" / "discovery_rounds.json").read_text())
    assert [(r["round"], r["hypotheses"], r["novel"], r["inputs"]) for r in rounds] == [
        (1, 2, 1, ["transcription_factors"]), (2, 1, 0, []), (3, 1, 0, [])]
    s = discovery.summary(lab)
    assert s["rounds"] == 3 and s["hypotheses"] == 4 and s["hypotheses_naming_an_unread_input"] == 1
    assert s["inputs_proposed"] == ["transcription_factors"] and s["dry_at_round"] == 3 and s["rounds_counted"] == 3
    assert s["dry_rule"].startswith("2 consecutive counted rounds")
    assert s["features_scored_for_derivability"] == 0  # nothing ran
    assert all(r["counted"] for r in rounds)

    # an unread input resets the count, and a round not asked for new features (the EXPLOIT focus of a concurrent
    # round) or proposing none (combine actions only) is recorded but not counted
    lab2 = lab_factory(schedule__discovery=True, schedule__discovery_dry_rounds=2)
    lab2.record_analytic_baselines()
    combine = {"synthesis": "s", "hypotheses": [
        {"title": "c", "hypothesis": "adding both helpful features improves the model", "category": "exploit",
         "rationale": "A biologically motivated test fixture rationale.", "action": "combine",
         "add_features": ["control_mean"]}]}
    prov2 = _FixedPlanner([plans[1], plans[3], plans[1], plans[1], combine, plans[1]])
    planner2 = Planner(lab2, prov2, [])
    assert planner2.refill(1) and planner2.novel_dry == 1
    assert planner2.refill(1) and planner2.novel_dry == 0
    assert planner2.refill(1, focus="EXPLOIT: improve the current best model") and planner2.novel_dry == 0
    assert planner2.refill(1, focus="RISKY: bolder hypotheses") and planner2.novel_dry == 1 and not planner2.dry()
    planner2.refill(1)  # the combine-only plan: queued or not, it is not counted
    assert planner2.novel_dry == 1 and not planner2.dry()
    assert planner2.refill(1) and planner2.novel_dry == 2 and planner2.dry()
    rows2 = json.loads((lab2.run_dir / "planner" / "discovery_rounds.json").read_text())
    assert [r["counted"] for r in rows2] == [True, True, False, True, False, True]
    assert discovery.summary(lab2)["dry_at_round"] == 6 and discovery.summary(lab2)["rounds_counted"] == 4
    assert discovery.dry_round(rows2, 2) == 6 and discovery.dry_round(rows2[:5], 2) is None
    # a torn ledger costs no planner call and no summary
    (lab2.run_dir / "planner" / "discovery_rounds.json").write_text("{not json")
    assert discovery.summary(lab2)["rounds"] == 0
    assert discovery.record_round(lab2, 7, [["prior_network"]], 1)["round"] == 7
    assert len(json.loads((lab2.run_dir / "planner" / "discovery_rounds.json").read_text())) == 1


# ------------------------------------------------------------------------------------------------------- end to end
def test_controller_run_in_discovery_mode(lab_factory):
    lab = lab_factory(schedule__discovery=True, schedule__max_planner_calls=3)
    ctl = Controller(lab, workers=2, seconds=60, worker_provider=MockProvider(), planner_provider=ScriptedPlanner(),
                     quiet=True)
    summary = ctl.run()
    assert summary["experiments_completed"] >= 3
    d = summary["discovery"]
    assert d["enabled"] and d["rounds"] >= 1 and d["rounds"] == len(json.loads(
        (lab.run_dir / "planner" / "discovery_rounds.json").read_text()))
    assert d["features_scored_for_derivability"] >= 1
    assert all(-1 <= r["r2"] <= 1 for r in d["derived_features"] + d["new_input_features"])
    assert all(r["r2"] >= d["derived_r2_threshold"] for r in d["derived_features"])
    assert all(r["r2"] < d["derived_r2_threshold"] for r in d["new_input_features"])
    assert len(d["derived_features"]) + len(d["new_input_features"]) == d["features_scored_for_derivability"]
    states = sorted((lab.run_dir / "planner").glob("state_*.txt"))
    assert states and all(discovery.EVIDENCE_HEADING in s.read_text() and "## INPUTS UNEXPLORED" in s.read_text()
                          and "UNEXPLORED IDEA AREAS" not in s.read_text() for s in states)
    assert any("training perturbations out of fold only" in s.read_text() for s in states[1:] or states)
    assert d["evidence_files"] and all(re.fullmatch(r"discovery_EXP_\w+\.json", f) for f in d["evidence_files"])
    # no default-mode field is lost, and the summary on disk is the one returned
    assert summary["planner"]["configured"] == "scripted:scripted" and summary["best"]["score"] >= summary["baseline"]["score"]
    assert json.loads((lab.run_dir / "summary.json").read_text())["discovery"] == d
