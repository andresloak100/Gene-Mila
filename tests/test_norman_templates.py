"""Prompts, scripted control and smoke test for bundles with pairs of genes or a recorded modality (docs/NORMAN_PLAN.md
section 4, items 9 to 11): the DATASET line, the pair notes of the planner and worker prompts, the idea bank, the
additive hypothesis and template, the order-free `similar` template, and a smoke test that samples and checks pairs.

A single-target bundle without a modality (Adamson's kind; the session's synthetic dataset) gets every prompt, the
scripted hypothesis list, the template choice and the unchanged templates byte for byte as the code at commit b63491d
produced them, frozen in tests/data/adamson_text_b63491d.json (captured from that code before these edits), and the
changed templates give it exactly the values the frozen ones give."""

import json
from pathlib import Path

import numpy as np
import pytest

from genemila import prompts
from genemila.data.bundle import export_public, split_id_for, write_bundle
from genemila.features import registry
from genemila.features.api import FeatureContext
from genemila.pipeline import smoke
from genemila.providers.mock import (NEUTRAL_HYPOTHESIS_TEXT, NEUTRAL_TEMPLATE_TEXT, PAIR_HYPOTHESES,
                                     SCRIPTED_HYPOTHESES, TEMPLATES, MockProvider, ScriptedPlanner, _pick_template,
                                     external_hypotheses, scripted_hypotheses)
from genemila.research_state import IDEA_BANK, PAIR_IDEAS, build_state, idea_bank, render_state

FROZEN = json.loads((Path(__file__).resolve().parent / "data" / "adamson_text_b63491d.json").read_text())
MIX = {"explore": 0.65, "exploit": 0.25, "risky": 0.10}
CHANGED = {"similar", "external_direct", "external_knn", "external_krr"}   # the templates these items edit


def _drain(planner, state, rounds=4):
    texts = []
    for _ in range(rounds):
        texts.append(planner.propose(state, 8, MIX, 0).text)
        if not json.loads(texts[-1])["hypotheses"]:
            break
    return texts


def make_pairs_bundle(out: Path, pairs: bool = True, modality: str | None = "CRISPRa", seed: int = 0) -> Path:
    """A small two-gene screen: 16 genes with a single each and, with pairs, 24 random pairs whose change is the sum
    of their singles' plus a little noise, keyed by their genes sorted and joined with '+'. Genes G12 to G15 are held
    out with their single and every pair holding one (the most held-out set of a pair's genes), and four pairs of
    two training genes are held out too, so training has singles and pairs and so has each held-out set."""
    rng = np.random.default_rng(seed)
    n_genes = 60
    genes = [f"G{i:02d}" for i in range(n_genes)]
    base = rng.uniform(0.5, 3.0, n_genes)
    singles = genes[:16]
    effect = {}
    for i, g in enumerate(singles):
        d = np.zeros(n_genes)
        d[i] = 1.5
        hit = rng.choice(np.arange(16, n_genes), size=10, replace=False)
        d[hit] = rng.normal(0, 0.6, size=10)
        effect[g] = d
    targets = {g: [g] for g in singles}
    means = {g: base + effect[g] + rng.normal(0, 0.03, n_genes) for g in singles}
    while pairs and len(targets) < 16 + 24:
        a, b = sorted(str(g) for g in rng.choice(singles, size=2, replace=False))
        if f"{a}+{b}" not in targets:
            targets[f"{a}+{b}"] = [a, b]
            means[f"{a}+{b}"] = base + effect[a] + effect[b] + rng.normal(0, 0.1, n_genes)
    held = {g: ("val1" if i % 2 == 0 else "val2") for i, g in enumerate(singles[12:])}
    rank = ("train", "val1", "val2")
    part = {p: max((held.get(g, "train") for g in targets[p]), key=rank.index) for p in sorted(targets)}
    for i, p in enumerate([p for p in sorted(targets) if len(targets[p]) == 2 and part[p] == "train"][:4]):
        part[p] = rank[1 + i % 2]
    splits = {s: sorted(p for p in part if part[p] == s) for s in rank}
    splits["seed"] = seed
    splits["split_id"] = split_id_for(splits)
    control = np.maximum(base + rng.normal(0, 0.3, size=(300, n_genes)), 0)
    sets = {f"SET_{k}": sorted({singles[2 * k], singles[2 * k + 1], *map(str, rng.choice(genes[16:], 6, False))})
            for k in range(8)}
    edges = [[g, str(t), float(rng.choice([-1, 1]))] for g in singles for t in rng.choice(genes[16:], 3, False)]
    return write_bundle(out, "norman_toy", genes, control, means, {p: 50 for p in targets}, targets, splits,
                        knowledge={"gene_sets.json": sets, "prior_network.json": edges},
                        extra_meta={"modality": modality} if modality else None)


def add_screen(public: Path, sign: int = -1, drop: str = "G00") -> dict:
    """An external screen knowledge file in a public directory, shaped like build_external_screen's output: per single
    gene but `drop`, the opposite of its true change plus noise (a screen of the other modality), three genes
    unmeasured, and a top-level sign."""
    ctx = FeatureContext(public)
    z = np.load(public / "public.npz")
    rng = np.random.default_rng(3)
    unmeasured = {5, 21, 40}
    perts = {}
    for p, m in zip([str(q) for q in z["train_perts"]], z["train_means"].astype(float)):
        if "+" not in p and p != drop:
            d = -(m - ctx.control_mean) + rng.normal(0, 0.05, ctx.n_genes)
            perts[p] = {"n_cells": 40, "labels": [p],
                        "delta": [None if j in unmeasured else round(float(v), 5) for j, v in enumerate(d)]}
    for g in [t for p in ctx.perts for t in ctx.target_genes(p)]:   # held-out genes: a noisy row of their own
        if g not in perts and g != drop:
            perts[g] = {"n_cells": 40, "labels": [g],
                        "delta": [None if j in unmeasured else round(float(v), 5)
                                  for j, v in enumerate(rng.normal(0, 0.5, ctx.n_genes))]}
    screen = {"description": "CRISPRi screen deltas, test fixture.", "sign": sign,
              "source": {"modality": "CRISPRi", "bundle_modality": "CRISPRa"}, "genes": ctx.genes,
              "measured": [j not in unmeasured for j in range(ctx.n_genes)],
              "control": {"n_cells": 100, "mean": [0.0] * ctx.n_genes}, "perts": perts,
              "bundle_targets_missing": [drop]}
    (public / "knowledge" / "ext_screen.json").write_text(json.dumps(screen))
    return screen


@pytest.fixture(scope="module")
def pairs_public(tmp_path_factory):
    root = tmp_path_factory.mktemp("norman_templates")
    pub = export_public(make_pairs_bundle(root / "bundle"), root / "pub")
    add_screen(pub)
    return pub


def _plugin(tmp_path, code: str, name: str) -> Path:
    d = tmp_path / f"plugins_{name}"
    d.mkdir(exist_ok=True)
    (d / f"{name}.py").write_text(code)
    return d


def _compute(tmp_path, code: str, name: str, ctx: FeatureContext, perts=None) -> np.ndarray:
    registry.load_plugins(_plugin(tmp_path, code, name))
    return np.asarray(registry.get(name)().compute(ctx, perts or ctx.perts, dict(registry.get(name).params)))


def _reversed(ctx: FeatureContext) -> FeatureContext:
    """The same context with every perturbation's targets listed in reverse order."""
    out = FeatureContext(ctx.public_dir)
    out._targets = {p: list(reversed(v)) for p, v in out._targets.items()}
    return out


# ------------------------------------------------------------------- Adamson: byte for byte as before
def test_adamson_planner_and_worker_prompts_are_unchanged(lab_factory):
    assert prompts.PLANNER_SYSTEM == FROZEN["planner_system"] and prompts.PLANNER_SCHEMA == FROZEN["planner_schema"]
    assert prompts.WORKER_SYSTEM == FROZEN["worker_system"] and prompts.FEATURE_API_DOC == FROZEN["feature_api_doc"]
    assert prompts.EXAMPLE_FEATURE == FROZEN["example_feature"] and prompts.SUMMARY_SYSTEM == FROZEN["summary_system"]
    assert prompts.planner_user(FROZEN["state_example"], 8, MIX) == FROZEN["planner_user_example"]
    assert prompts.planner_user("<<STATE>>", 8, MIX) == FROZEN["planner_user_placeholder"]
    task = FROZEN["task"]
    assert prompts.worker_implement(task) == FROZEN["worker_implement"]
    assert prompts.worker_diagnose(task, "import numpy as np\n", "Traceback: ValueError: shape") == \
        FROZEN["worker_diagnose"]
    # a live single-target lab: its DATASET line, idea areas, planner message and worker message
    lab = lab_factory()
    lab.record_analytic_baselines()
    assert lab.data_summary() == FROZEN["synthetic_data_summary"]
    state = build_state(lab)
    assert state["dataset"] == FROZEN["synthetic_data_summary"]
    assert state["unexplored_idea_areas"] == FROZEN["synthetic_unexplored_idea_areas"]
    assert [[i, list(k)] for i, k in IDEA_BANK] == FROZEN["idea_bank"] and idea_bank(False, False) is IDEA_BANK
    text = render_state(state)
    assert prompts.planner_user(text, 8, MIX) == FROZEN["planner_user_placeholder"].replace("<<STATE>>", text)
    live = {**task, "data_summary": lab.data_summary()}
    assert prompts.worker_implement(live) == FROZEN["worker_implement"].replace(task["data_summary"],
                                                                                 lab.data_summary())
    assert not any(any(prompts.dataset_flags(t).values()) for t in (text, lab.data_summary(), task["data_summary"]))


def test_adamson_scripted_hypotheses_and_template_choice_are_unchanged(lab_factory):
    assert [list(h) for h in SCRIPTED_HYPOTHESES] == FROZEN["scripted_hypotheses"]
    assert [list(h) for h in external_hypotheses(["ext_screen"])] == FROZEN["external_hypotheses_ext_screen"]
    assert _drain(ScriptedPlanner(), FROZEN["state_example"]) == FROZEN["scripted_rounds_example"]
    assert _drain(ScriptedPlanner(external=["ext_screen"]), FROZEN["state_example"]) == \
        FROZEN["scripted_rounds_example_external"]
    lab = lab_factory()
    lab.record_analytic_baselines()
    planner = ScriptedPlanner()
    assert _drain(planner, render_state(build_state(lab)), 10) == FROZEN["scripted_rounds_live"]
    assert planner.hypotheses == SCRIPTED_HYPOTHESES and planner.pairs is False and planner.modality is False
    assert {h: _pick_template(h) for h in FROZEN["pick_template"]} == FROZEN["pick_template"]
    # every template these items leave alone is byte-identical, and the mock worker writes it as before
    assert set(FROZEN["templates"]) | {"additive"} == set(TEMPLATES)
    for key, code in FROZEN["templates"].items():
        assert (TEMPLATES[key] == code) == (key not in CHANGED), key
    for title, cat, name, desc, why in SCRIPTED_HYPOTHESES:
        task = {"new_feature": {"name": name, "description": desc, "implementation_hint": desc},
                "data_summary": lab.data_summary()}
        key = _pick_template(f"{name} {desc} {desc}")
        want = FROZEN["templates"][key] if key not in CHANGED else TEMPLATES[key]
        assert MockProvider().implement(task, 1000).text == f"```python\n{want.format(name=name, knowledge='')}```"


def test_additive_keywords_leave_a_single_target_bundle_s_template_choice_alone(tmp_path):
    """The additive template's keywords are read only for a bundle with pairs: on a single-target line (Adamson's;
    with or without a modality) a text that says "additive model" or "additivity" gets the template it got at
    b63491d, through the mock worker too, and on a pair line the same text gets the additive one."""
    from genemila.providers.mock import _code
    adamson = FROZEN["synthetic_data_summary"]
    bundle = make_pairs_bundle(tmp_path / "bundle")
    pairs_line = prompts.dataset_line(json.loads((bundle / "manifest.json").read_text()),
                                      json.loads((bundle / "knowledge" / "targets.json").read_text()),
                                      json.loads((bundle / "splits.json").read_text())["train"])
    single = make_pairs_bundle(tmp_path / "single", pairs=False, modality="CRISPRa")
    modality_line = prompts.dataset_line(json.loads((single / "manifest.json").read_text()),
                                         json.loads((single / "knowledge" / "targets.json").read_text()),
                                         json.loads((single / "splits.json").read_text())["train"])
    was = {"additive model of similar perturbations' responses (kNN transfer)": "similar",
           "test additivity of neighbour transfer": "similar", "additive single-gene network effects": "network",
           "pathway additivity of module scores": "module", "additivity of target expression": "target_level"}
    for text, key in was.items():
        assert _pick_template(text) == key and _pick_template(text, True) == "additive", text
        plain = TEMPLATES[key].format(name="x", knowledge="")
        assert _code(text, "x", adamson) == _code(text, "x") == plain, text
        neutral = plain
        for old, new in NEUTRAL_TEMPLATE_TEXT.get(key, []):   # a modality rewords the template, never changes it
            neutral = neutral.replace(old, new)
        assert _code(text, "x", modality_line) == neutral, text
        assert _code(text, "x", pairs_line) == TEMPLATES["additive"].format(name="x", knowledge="")
    text = "additive model of similar perturbations"
    assert _code(text, "x", adamson) == TEMPLATES["similar"].format(name="x", knowledge="")
    task = {"new_feature": {"name": "pert_sim_e20", "description": f"{text}' responses (kNN transfer)",
                            "implementation_hint": "weighted kNN over co-expressed targets"}, "data_summary": adamson}
    assert MockProvider().implement(task, 1000).text == \
        f"```python\n{TEMPLATES['similar'].format(name='pert_sim_e20', knowledge='')}```"
    # the frozen choices of b63491d hold with and without the pair flag off
    assert {h: _pick_template(h, False) for h in FROZEN["pick_template"]} == FROZEN["pick_template"]


def test_similar_gives_the_old_values_on_a_single_target_bundle(dataset, tmp_path):
    """The similar fix changes nothing for single targets: every perturbation's values on the synthetic bundle equal
    those of the template as it was at b63491d, bit for bit (the external templates: test_external_screen_control)."""
    pub = export_public(dataset, tmp_path / "pub")
    old = _compute(tmp_path, FROZEN["templates"]["similar"].format(name="old_similar"), "old_similar",
                   FeatureContext(pub))
    new = _compute(tmp_path, TEMPLATES["similar"].format(name="new_similar"), "new_similar", FeatureContext(pub))
    assert np.array_equal(old, new) and np.abs(new).sum() > 0


# ------------------------------------------------------------------- Norman: prompts and idea bank
def test_dataset_line_and_prompts_for_a_bundle_with_pairs(tmp_path, code_repo):
    from conftest import make_cfg
    from genemila.lab import Lab

    bundle = make_pairs_bundle(tmp_path / "bundle")
    cfg = make_cfg(tmp_path)
    cfg["run"]["data_dir"] = str(bundle)
    lab = Lab(cfg, tmp_path / "run", bundle, repo=code_repo)
    try:
        splits = json.loads((bundle / "splits.json").read_text())
        n_pairs = sum("+" in p for p in splits["train"])
        assert n_pairs and n_pairs < len(splits["train"])
        line = lab.data_summary()
        assert line == (f"norman_toy: 60 genes, 300 control cells, {len(splits['train'])} training perturbations "
                        f"({len(splits['train']) - n_pairs} single genes, {n_pairs} pairs of two genes; "
                        f"{prompts.PAIR_KEYS}); modality CRISPRa (CRISPR activation: a perturbation raises its target "
                        "genes' expression); predict unseen perturbations, single genes and pairs.")
        lab.record_analytic_baselines()
        state = build_state(lab)
        text = render_state(state)
        assert state["dataset"] == line and prompts.dataset_flags(text) == {"pairs": True, "modality": True}
        # the additivity idea stays unexplored after baseline_additive ("... (additive model).") has run
        assert PAIR_IDEAS[0][0] in state["unexplored_idea_areas"]
        assert "target perturbation magnitude (how far p moves its own targets)" in state["unexplored_idea_areas"]
        assert "target knockdown magnitude" not in state["unexplored_idea_areas"]
        msg = prompts.planner_user(text, 8, MIX)
        assert prompts.PAIRS_PLANNER_NOTE in msg and "a feature-set combination): existing feature names" in msg
        assert msg.startswith(f"RESEARCH STATE\n{text}\n\n")
        task = {**FROZEN["task"], "data_summary": line}
        for out in (prompts.worker_implement(task), prompts.worker_diagnose(task, "x = 1\n", "error")):
            assert prompts.PAIRS_API_NOTE in out
            assert prompts.TARGET_API_LINE + prompts.PAIRS_API_NOTE + "  ctx.train_delta(exclude=p)" in out
    finally:
        lab.close()


def test_modality_alone_and_quoted_words_change_only_what_they_should(tmp_path):
    """A single-target bundle with a modality gets the modality in its DATASET line and the modality-neutral idea,
    but no pair note or additivity idea; the words of a pair line quoted elsewhere in a state change nothing."""
    bundle = make_pairs_bundle(tmp_path / "bundle", pairs=False, modality="CRISPRi")
    manifest = json.loads((bundle / "manifest.json").read_text())
    targets = json.loads((bundle / "knowledge" / "targets.json").read_text())
    train = json.loads((bundle / "splits.json").read_text())["train"]
    line = prompts.dataset_line(manifest, targets, train)
    assert line == ("norman_toy: 60 genes, 300 control cells, 12 training perturbations (single-gene targets); "
                    "modality CRISPRi (CRISPR interference: a perturbation lowers its target genes' expression); "
                    "predict unseen perturbations.")
    assert prompts.dataset_flags(line) == {"pairs": False, "modality": True}
    assert prompts.planner_user(f"## DATASET\n{line}", 8, MIX) == \
        FROZEN["planner_user_placeholder"].replace("<<STATE>>", f"## DATASET\n{line}")
    ideas = [i for i, _ in idea_bank(False, True)]
    assert len(ideas) == len(IDEA_BANK) and "target perturbation magnitude (how far p moves its own targets)" in ideas
    assert prompts.dataset_line({**manifest, "modality": "MyScreen"}, targets, train).endswith(
        "(single-gene targets); modality MyScreen; predict unseen perturbations.")
    quoted = f"## DATASET\n{FROZEN['synthetic_data_summary']}\n## IN FLIGHT\n- {prompts.PAIR_KEYS}; modality X"
    assert prompts.dataset_flags(quoted) == {"pairs": False, "modality": False}
    assert prompts.planner_user(quoted, 8, MIX) == FROZEN["planner_user_placeholder"].replace("<<STATE>>", quoted)


# ------------------------------------------------------------------- Norman: scripted control
def test_scripted_planner_adds_the_additive_hypothesis_only_for_pairs(tmp_path):
    bundle = make_pairs_bundle(tmp_path / "bundle")
    manifest = json.loads((bundle / "manifest.json").read_text())
    targets = json.loads((bundle / "knowledge" / "targets.json").read_text())
    line = prompts.dataset_line(manifest, targets, json.loads((bundle / "splits.json").read_text())["train"])
    planner = ScriptedPlanner(external=["ext_screen"])
    assert planner.hypotheses == SCRIPTED_HYPOTHESES + external_hypotheses(["ext_screen"])   # until it reads a state
    first = json.loads(planner.propose(f"## DATASET\n{line}\n## BASELINES\n- x", 20, MIX, 0).text)["hypotheses"]
    names = [h["new_feature"]["name"] for h in first]
    assert names == [h[2] for h in SCRIPTED_HYPOTHESES] + ["additive_singles", "external_direct_ext_screen",
                                                           "external_knn_ext_screen", "external_krr_ext_screen"]
    assert planner.hypotheses == scripted_hypotheses(["ext_screen"], pairs=True, neutral=True)
    # titles and rationales say perturbation, never knockdown or knockout; descriptions are untouched
    for h, (title, cat, name, desc, why) in zip(first, SCRIPTED_HYPOTHESES + PAIR_HYPOTHESES +
                                                external_hypotheses(["ext_screen"])):
        assert h["new_feature"]["description"] == desc and h["hypothesis"] == f"Adding {desc} improves prediction " \
                                                                               "of unseen perturbations."
        assert not any(w in (h["title"] + h["rationale"]).lower() for w in ("knock", "knocked"))
    for old, new in NEUTRAL_HYPOTHESIS_TEXT:
        assert any(old in t for h in SCRIPTED_HYPOTHESES + external_hypotheses(["k"]) for t in (h[0], h[4])), old
    # explicit flags, and a modality without pairs: the wording but not the additive hypothesis
    assert ScriptedPlanner(pairs=True).hypotheses[len(SCRIPTED_HYPOTHESES)][2] == "additive_singles"
    assert [h[2] for h in ScriptedPlanner(modality=True).hypotheses] == [h[2] for h in SCRIPTED_HYPOTHESES]
    # the additive text reaches its own template, before `similar` and away from `variance`, on a bundle with pairs
    title, cat, name, desc, why = PAIR_HYPOTHESES[0]
    assert _pick_template(f"{name}_e14 {desc} {desc}", True) == "additive" and _pick_template(desc, True) == "additive"
    assert _pick_template(desc) != "additive"   # the keywords are not read for any other bundle
    task = {"new_feature": {"name": name, "description": desc, "implementation_hint": desc}, "data_summary": line}
    assert TEMPLATES["additive"].format(name=name, knowledge="") in MockProvider().implement(task, 1000).text


def test_neutral_template_text_is_used_only_for_pairs_or_a_modality(tmp_path):
    bundle = make_pairs_bundle(tmp_path / "bundle", pairs=False, modality="CRISPRa")
    manifest = json.loads((bundle / "manifest.json").read_text())
    line = prompts.dataset_line(manifest, json.loads((bundle / "knowledge" / "targets.json").read_text()),
                                json.loads((bundle / "splits.json").read_text())["train"])
    for key, edits in NEUTRAL_TEMPLATE_TEXT.items():
        code = TEMPLATES[key].format(name="f", knowledge="ext_screen")
        for old, new in edits:
            assert code.count(old) == 1 and new not in code, (key, old)   # each edit lands exactly once
    hyps = SCRIPTED_HYPOTHESES + external_hypotheses(["ext_screen"])
    for title, cat, name, desc, why in hyps:
        nf = {"name": name, "description": desc, "implementation_hint": desc}
        key = _pick_template(f"{name} {desc} {desc}")
        plain = TEMPLATES[key].format(name=name, knowledge=desc.split()[-1] if "external" in key else "")
        assert MockProvider().implement({"new_feature": nf, "data_summary": FROZEN["synthetic_data_summary"]},
                                        1000).text == f"```python\n{plain}```"
        neutral = MockProvider().implement({"new_feature": nf, "data_summary": line}, 1000).text
        want = plain
        for old, new in NEUTRAL_TEMPLATE_TEXT.get(key, []):
            want = want.replace(old, new)
        assert neutral == f"```python\n{want}```" and "knocked-out" not in neutral and "after knockout" not in neutral


# ------------------------------------------------------------------- Norman: templates
def test_additive_template_is_the_leave_one_out_additive_model(pairs_public, tmp_path):
    """A pair whose two singles are in training is exactly control + their two training changes; a training single is
    the mean of the other training singles (its own label left out); a held-out single is the mean training single;
    and swapping a pair's target order changes nothing."""
    ctx = FeatureContext(pairs_public)
    out = _compute(tmp_path, TEMPLATES["additive"].format(name="additive_f"), "additive_f", ctx)[:, :, 0]
    delta = dict(zip(ctx.train_perts, ctx._train_delta))
    singles = [p for p in ctx.train_perts if "+" not in p]
    checked = set()
    for i, p in enumerate(ctx.perts):
        a, *rest = ctx.target_genes(p)
        if rest and all(g in delta for g in (a, *rest)):
            np.testing.assert_allclose(out[i], delta[a] + delta[rest[0]], rtol=1e-12, atol=1e-12, err_msg=p)
            checked.add("train pair" if p in delta else "held-out pair")
        elif not rest and p in delta:
            np.testing.assert_allclose(out[i], np.mean([delta[q] for q in singles if q != p], axis=0), rtol=1e-12)
            checked.add("train single")
        elif not rest:
            np.testing.assert_allclose(out[i], np.mean([delta[q] for q in singles], axis=0), rtol=1e-12)
            checked.add("held-out single")
    assert checked == {"train pair", "held-out pair", "train single", "held-out single"}
    rev = _compute(tmp_path, TEMPLATES["additive"].format(name="additive_r"), "additive_r", _reversed(ctx))
    assert np.array_equal(rev[:, :, 0], out)


def test_similar_template_takes_unordered_target_sets_of_any_size(dataset, tmp_path):
    """mock.py's similar paired targets by position (A with C, B with D) and raised IndexError for 2 against 3
    targets; it now takes the mean over the whole block of their correlations, whatever the order or sizes."""
    pub = export_public(dataset, tmp_path / "pub")
    targets = json.loads((pub / "knowledge" / "targets.json").read_text())
    z = np.load(pub / "public.npz")
    train, genes = [str(p) for p in z["train_perts"]], [str(g) for g in z["genes"]]
    held = [str(p) for p in z["perts"] if str(p) not in set(train)]
    targets[train[0]] += [genes[-1], genes[-2]]        # three targets
    targets[train[1]] += [genes[-3]]                   # two
    targets[held[0]] += [genes[-4]]                    # two, outside training
    (pub / "knowledge" / "targets.json").write_text(json.dumps(targets))
    ctx = FeatureContext(pub)
    out = _compute(tmp_path, TEMPLATES["similar"].format(name="sim_f"), "sim_f", ctx)
    rev = _compute(tmp_path, TEMPLATES["similar"].format(name="sim_r"), "sim_r", _reversed(ctx))
    np.testing.assert_allclose(out, rev, rtol=1e-12, atol=1e-14)
    # the block mean for a 2-by-3 pair of target sets, by hand
    t0, t1 = ctx.target_indices(train[0]), ctx.target_indices(train[1])
    assert len(t0) == 3 and len(t1) == 2
    assert np.isclose(np.abs(ctx.gene_corr[np.ix_(t1, t0)]).mean(),
                      np.mean([abs(ctx.gene_corr[a, b]) for a in t1 for b in t0]))


# ------------------------------------------------------------------- Norman: smoke test (item 10)
PAIR_ONLY = '''import numpy as np
from genemila.features.api import Feature, register

@register
class F(Feature):
    name = "{name}"
    description = "1 on the targets of a pair of genes, else 0 (0 on every single)."
    rationale = "Test fixture: a feature only pairs move."
    inputs = ["targets"]
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            t = ctx.target_indices(p)
            if len(set(t)) > 1:
                out[i, t, 0] = 1.0
        return out
'''

FIRST_TARGET = '''import numpy as np
from genemila.features.api import Feature, register

@register
class F(Feature):
    name = "{name}"
    description = "Control correlation of g with p's first listed target only (wrong for a pair)."
    rationale = "Test fixture: reads [0]."
    inputs = ["control_cells", "targets"]
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            t = ctx.target_indices(p)
            if t:
                out[i, :, 0] = ctx.gene_corr[t[0]]
        return out
'''

PAIR_LEAK = '''import numpy as np
from genemila.features.api import Feature, register

@register
class F(Feature):
    name = "{name}"
    description = "Mean training response, plus a pair's own training label (leaks for pairs only)."
    rationale = "Test fixture: leaks on pairs."
    inputs = ["train_delta", "targets"]
    dim = 1

    def compute(self, ctx, perts, params):
        names, d = ctx.train_delta()
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            _, rest = ctx.train_delta(exclude=p)
            out[i, :, 0] = rest.mean(axis=0)
            if len(ctx.target_genes(p)) > 1 and p in names:
                out[i, :, 0] += d[names.index(p)]
        return out
'''


def _smoke(public, tmp_path, code, name):
    return smoke(name, public, _plugin(tmp_path, code.format(name=name), name), tmp_path / f"smoke_{name}")


def test_smoke_samples_pairs_and_checks_their_order_and_labels(pairs_public, dataset, tmp_path):
    single_pub = export_public(dataset, tmp_path / "single_pub")
    # a feature zero on every single: constant on Adamson's sample, informative once pairs are sampled
    r = _smoke(pairs_public, tmp_path, PAIR_ONLY, "pair_only")
    assert r["status"] == "ok", r
    r = _smoke(single_pub, tmp_path, PAIR_ONLY, "pair_only_single")
    assert r["status"] == "failed" and r["problems"] == ["feature is constant across all rows (no information)"]
    # reading only the first target: fine for singles, refused for pairs
    assert _smoke(single_pub, tmp_path, FIRST_TARGET, "first_single")["status"] == "ok"
    r = _smoke(pairs_public, tmp_path, FIRST_TARGET, "first_pair")
    assert r["status"] == "failed" and len(r["problems"]) == 1 and "order of a pair's target genes" in r["problems"][0]
    # leaking a pair's own label: invisible on Adamson's sample, caught on the training pair
    assert _smoke(single_pub, tmp_path, PAIR_LEAK, "leak_single")["status"] == "ok"
    r = _smoke(pairs_public, tmp_path, PAIR_LEAK, "leak_pair")
    first_pair = next(p for p in FeatureContext(pairs_public).train_perts if "+" in p)
    assert r["status"] == "failed" and r["problems"] == [
        f"label leakage: features for training perturbation {first_pair} depend on its own label "
        "(use ctx.train_delta(exclude=p))"]


@pytest.mark.parametrize("key", sorted(CHANGED))
def test_the_templates_as_they_were_fail_the_pair_smoke_test(key, pairs_public, tmp_path):
    """The checks can fail: at b63491d the external templates took a pair's first target with a row and `similar`
    matched two pairs' targets by position, and the smoke test refuses each on a bundle with pairs."""
    code = FROZEN["templates"][key].replace("{knowledge}", "ext_screen")
    r = _smoke(pairs_public, tmp_path, code, f"old_{key}")
    assert r["status"] == "failed" and len(r["problems"]) == 1, r
    assert r["problems"][0].startswith("output depends on the order of a pair's target genes")


@pytest.mark.parametrize("key", sorted(set(TEMPLATES) - {"variance"}))
def test_every_template_passes_the_smoke_test_on_a_bundle_with_pairs(key, pairs_public, tmp_path):
    """Order-free, leak-free and informative on the pair sample: every template the scripted control can write (the
    variance template is the same for every perturbation and is checked on the single-target bundle)."""
    code = TEMPLATES[key].replace("{knowledge}", "ext_screen")
    r = _smoke(pairs_public, tmp_path, code, f"tpl_{key}")
    assert r["status"] == "ok", (key, r)


def test_prompts_doc_quotes_the_norman_text_verbatim():
    """docs/PROMPTS.md quotes the pair notes and the additive hypothesis as the code writes them."""
    doc = (Path(__file__).resolve().parent.parent / "docs" / "PROMPTS.md").read_text()
    assert prompts.PAIRS_PLANNER_NOTE in doc and prompts.PAIRS_API_NOTE in doc
    title, cat, name, desc, why = PAIR_HYPOTHESES[0]
    assert f"**{title}** (`{name}`, category {cat}). Hypothesis sent to the worker: \"Adding {desc} improves " \
           f"prediction of unseen perturbations.\" Rationale: \"{why}\"" in doc
    for old, new in NEUTRAL_HYPOTHESIS_TEXT:
        assert f'"{old}" becomes "{new}"' in " ".join(doc.split()), old
