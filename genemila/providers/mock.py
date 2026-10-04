"""Offline providers for tests and dry runs.

MockProvider writes real, working feature code from a small template library
(selected by keywords in the requested feature), with optional injected
failures, so the full loop can be exercised without any API. ScriptedPlanner
proposes a fixed sequence of hypotheses in the planner JSON format.
"""

from __future__ import annotations

import json
import random
import threading
import time

from .base import ProviderError, AgentProvider, LLMResponse, Usage

TEMPLATES = {
    "coexpr": '''import numpy as np
from genemila.features.api import Feature, register

@register
class F(Feature):
    name = "{name}"
    description = "Control-cell correlation between the perturbed target gene and gene g."
    rationale = "Genes co-expressed with the knocked-out gene likely share its regulatory program."
    inputs = ["control_cells", "targets"]
    params = {{"shrink": 0.0}}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            t = ctx.target_indices(p)
            if t:
                out[i, :, 0] = ctx.gene_corr[t].mean(axis=0) * (1 - params["shrink"])
        return out
''',
    "network": '''import numpy as np
from genemila.features.api import Feature, register

@register
class F(Feature):
    name = "{name}"
    description = "Signed prior-network edge from the perturbed gene to gene g, scaled by target expression."
    rationale = "Knocking out a regulator removes its activation (or repression) of known targets."
    inputs = ["prior_network", "targets", "control_cells"]
    dim = 1

    def compute(self, ctx, perts, params):
        edges = ctx.knowledge("prior_network") or []
        adj = {{}}
        for r, t, s in edges:
            if r in ctx.gene_index and t in ctx.gene_index:
                adj.setdefault(r, []).append((ctx.gene_index[t], s))
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            for g in ctx.target_genes(p):
                level = ctx.control_mean[ctx.gene_index[g]] if g in ctx.gene_index else 1.0
                for j, s in adj.get(g, []):
                    out[i, j, 0] += s * level
        return out
''',
    "module": '''import numpy as np
from genemila.features.api import Feature, register

@register
class F(Feature):
    name = "{name}"
    description = "Fraction of gene sets containing the target that also contain gene g, times control mean of g."
    rationale = "A knockout perturbs the pathway/module it belongs to."
    inputs = ["gene_sets", "targets", "control_cells"]
    dim = 1

    def compute(self, ctx, perts, params):
        sets = ctx.knowledge("gene_sets") or {{}}
        member = np.zeros((len(sets), ctx.n_genes))
        for k, genes in enumerate(sets.values()):
            member[k, [ctx.gene_index[g] for g in genes if g in ctx.gene_index]] = 1
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            t = ctx.target_indices(p)
            if t and len(sets):
                rows = member[:, t].max(axis=1) > 0
                if rows.any():
                    out[i, :, 0] = member[rows].mean(axis=0) * ctx.control_mean
        return out
''',
    "similar": '''import numpy as np
from genemila.features.api import Feature, register

@register
class F(Feature):
    name = "{name}"
    description = "Response of g averaged over the k training perturbations whose targets are most co-expressed with p's target (leave-one-out)."
    rationale = "Perturbations of functionally related genes produce similar transcriptional responses."
    inputs = ["train_delta", "control_cells", "targets"]
    params = {{"k": 5}}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            names, d = ctx.train_delta(exclude=p)
            t = ctx.target_indices(p)
            if not t:
                out[i, :, 0] = d.mean(axis=0)
                continue
            sims = np.array([np.abs(ctx.gene_corr[t, ctx.target_indices(q)]).mean() if ctx.target_indices(q) else 0.0
                             for q in names])
            top = np.argsort(-sims)[: int(params["k"])]
            w = sims[top] + 1e-6
            out[i, :, 0] = (w[:, None] * d[top]).sum(axis=0) / w.sum()
        return out
''',
    "pca": '''import numpy as np
from genemila.features.api import Feature, register

@register
class F(Feature):
    name = "{name}"
    description = "Product of target-gene and gene-g loadings on the top control PCs (one column per PC)."
    rationale = "Shared latent programs in control cells predict which genes move together after knockout."
    inputs = ["control_cells", "targets"]
    params = {{"n_pcs": 4}}
    dim = 4

    def compute(self, ctx, perts, params):
        k = int(params["n_pcs"])
        x = (ctx.control_cells - ctx.control_mean) / np.where(ctx.control_std > 0, ctx.control_std, 1)
        _, _, vt = np.linalg.svd(x, full_matrices=False)
        load = vt[:k].T  # genes x k
        out = np.zeros((len(perts), ctx.n_genes, k))
        for i, p in enumerate(perts):
            t = ctx.target_indices(p)
            if t:
                out[i] = load * load[t].mean(axis=0)
        return out[:, :, :self.dim] if out.shape[2] >= self.dim else np.pad(out, ((0, 0), (0, 0), (0, self.dim - k)))
''',
    "target_level": '''import numpy as np
from genemila.features.api import Feature, register

@register
class F(Feature):
    name = "{name}"
    description = "Control mean expression of g if g is the perturbed target, else 0."
    rationale = "Knockdown removes a fixed fraction of the target's expression, so the drop scales with its level."
    inputs = ["control_cells", "targets"]
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            t = ctx.target_indices(p)
            out[i, t, 0] = ctx.control_mean[t]
        return out
''',
    "variance": '''import numpy as np
from genemila.features.api import Feature, register

@register
class F(Feature):
    name = "{name}"
    description = "Control-cell standard deviation of gene g."
    rationale = "Variable genes are more responsive to perturbation."
    inputs = ["control_cells"]
    dim = 1

    def compute(self, ctx, perts, params):
        return np.broadcast_to(ctx.control_std[None, :, None], (len(perts), ctx.n_genes, 1)).copy()
''',
}

LEAKY = '''import numpy as np
from genemila.features.api import Feature, register

@register
class F(Feature):
    name = "{name}"
    description = "Leaky: uses p's own training label."
    rationale = "Deliberately wrong (test fixture)."
    dim = 1

    def compute(self, ctx, perts, params):
        names, d = ctx.train_delta()
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            if p in names:
                out[i, :, 0] = d[names.index(p)]
        return out
'''

CHEAT = '''import numpy as np
from genemila.features.api import Feature, register

@register
class F(Feature):
    name = "{name}"
    description = "Cheating: reads hidden labels."
    rationale = "Deliberately wrong (test fixture)."
    dim = 1

    def compute(self, ctx, perts, params):
        z = np.load("data/synthetic/private/val2.npz")
        return np.zeros((len(perts), ctx.n_genes, 1))
'''

SLOW = '''import numpy as np
from genemila.features.api import Feature, register

@register
class F(Feature):
    name = "{name}"
    description = "Pathologically slow feature (test fixture)."
    rationale = "Tests timeouts."
    dim = 1

    def compute(self, ctx, perts, params):
        x = 0.0
        while True:
            x += float(np.sum(np.random.rand(200)))
        return np.zeros((len(perts), ctx.n_genes, 1))
'''


def _pick_template(text: str) -> str:
    text = text.lower()
    for key, words in [("similar", ("similar", "knn", "neighbor", "neighbour", "transfer")),
                       ("network", ("network", "prior", "edge", "regulat", "tf ")),
                       ("module", ("module", "pathway", "gene_set", "gene set")),
                       ("pca", ("pca", "principal", "latent", "svd")),
                       ("coexpr", ("coexpr", "co-expr", "correlat")),
                       ("target_level", ("target_level", "knockdown", "self", "target expression")),
                       ("variance", ("varian", "dispersion", "std"))]:
        if any(w in text for w in words):
            return key
    return "variance"


class MockProvider(AgentProvider):
    name = "mock"

    def __init__(self, model: str = "mock", fail_rate: float = 0.0, seed: int = 0, latency_s: float = 0.0,
                 latency_jitter_s: float = 0.0):
        super().__init__(model)
        self.fail_rate = fail_rate
        self.rng = random.Random(seed)
        self.latency_s = latency_s
        self.latency_jitter_s = latency_jitter_s  # simulated LLM latency: latency_s + U(0, jitter), for load tests
        self.calls = 0
        self._lock = threading.Lock()
        self._errored: dict[str, int] = {}

    def _sleep(self) -> None:
        if self.latency_s or self.latency_jitter_s:
            with self._lock:
                extra = self.rng.random() * self.latency_jitter_s
            time.sleep(self.latency_s + extra)

    def _usage(self, prompt: str, out: str) -> Usage:
        return Usage(input_tokens=len(prompt) // 4, output_tokens=len(out) // 4, cached_tokens=0,
                     cost_usd=0.0, latency_s=self.latency_s)

    def complete(self, system: str, user: str, max_tokens: int) -> LLMResponse:
        self.calls += 1
        return LLMResponse(text="ok", usage=self._usage(system + user, "ok"), provider=self.name, model=self.model)

    def implement(self, task: dict, max_tokens: int) -> LLMResponse:
        self.calls += 1
        self._sleep()
        nf = task["new_feature"]
        hint = " ".join([nf["name"], nf.get("description", ""), nf.get("implementation_hint", "")])
        if "MOCK_CRASH" in hint:
            raise RuntimeError("simulated worker crash")
        if "MOCK_API_ERROR" in hint:  # transient provider error (429/5xx) on the first two calls for this feature
            with self._lock:
                n = self._errored.get(nf["name"], 0)
                self._errored[nf["name"]] = n + 1
            if n < 2:  # the gateway retries once itself, so the first logical call still fails
                raise ProviderError("simulated HTTP 503", retryable=True)
        if "MOCK_TRUNCATE" in hint:  # a reasoning model that spends the whole output limit thinking
            u = self._usage(json.dumps(task), "")
            u.output_tokens = max_tokens
            return LLMResponse(text="", usage=u, provider=self.name, model=self.model, finish_reason="length",
                               reasoning_tokens=max_tokens)
        if "MOCK_LEAK" in hint:
            code = LEAKY.format(name=nf["name"])
        elif "MOCK_CHEAT" in hint:
            code = CHEAT.format(name=nf["name"])
        elif "MOCK_SLOW" in hint:
            code = SLOW.format(name=nf["name"])
        elif "MOCK_BREAK" in hint or (self.fail_rate and self.rng.random() < self.fail_rate):
            code = "import numpy as np\nthis is not python(\n"
        else:
            code = TEMPLATES[_pick_template(hint)].format(name=nf["name"])
        text = f"```python\n{code}```"
        return LLMResponse(text=text, usage=self._usage(json.dumps(task), text), provider=self.name, model=self.model)

    def diagnose(self, task: dict, code: str, error: str, max_tokens: int) -> LLMResponse:
        self._sleep()
        nf = task["new_feature"]
        hint = " ".join([nf["name"], nf.get("description", ""), nf.get("implementation_hint", "")])
        if any(m in hint for m in ("MOCK_LEAK", "MOCK_CHEAT", "MOCK_SLOW", "MOCK_CRASH", "MOCK_TRUNCATE")):
            return self.implement(task, max_tokens)  # a model that repeats its mistake
        if "MOCK_BREAK_ALWAYS" in hint:
            code = "still broken(\n"
        else:
            code = TEMPLATES[_pick_template(hint.replace("MOCK_BREAK", ""))].format(name=nf["name"])
        text = f"```python\n{code}```"
        return LLMResponse(text=text, usage=self._usage(error, text), provider=self.name, model=self.model)


SCRIPTED_HYPOTHESES = [
    ("Target co-expression", "explore", "coexpr_target", "Pearson correlation in control cells between the target gene and gene g",
     "Genes co-expressed with the knocked-out gene share its regulatory program and should move with it."),
    ("Prior regulatory network", "explore", "prior_network_edge", "signed prior-network edge from the target to g, scaled by target expression",
     "Knocking out a TF removes its regulation of known targets."),
    ("Pathway membership", "explore", "shared_module", "gene-set co-membership of target and g (module/pathway)",
     "Knockouts disturb the pathway they belong to."),
    ("Similar perturbation transfer", "explore", "similar_pert_knn", "kNN transfer: average response of training perturbations with similar (co-expressed) targets",
     "Perturbations of functionally related genes have similar responses."),
    ("Target knockdown magnitude", "exploit", "target_level", "control mean of g if g is the target (target expression level)",
     "The knockdown drop scales with the target's baseline expression."),
    ("Latent program alignment", "risky", "pca_alignment", "PCA loadings product of target and gene g on top PCs",
     "Shared latent programs predict co-movement."),
    ("Gene variability", "explore", "control_variance", "control-cell std of gene g (variance)",
     "Variable genes respond more."),
]


class ScriptedPlanner(AgentProvider):
    """Deterministic planner used when no LLM planner is available, and in tests."""
    name = "scripted"

    def __init__(self, model: str = "scripted"):
        super().__init__(model)
        self.cursor = 0
        self.swept = False
        self.lasso = False
        self._lock = threading.Lock()  # planner rounds may run concurrently

    def complete(self, system: str, user: str, max_tokens: int) -> LLMResponse:
        return LLMResponse(text="{}", provider=self.name, model=self.model)

    def propose(self, research_state: str, n: int, mix: dict, max_tokens: int) -> LLMResponse:
        with self._lock:
            return self._propose(research_state, n)

    def _propose(self, research_state: str, n: int) -> LLMResponse:
        hyps = []
        while len(hyps) < n and self.cursor < len(SCRIPTED_HYPOTHESES):
            title, cat, name, desc, why = SCRIPTED_HYPOTHESES[self.cursor]
            hyps.append({"title": title, "hypothesis": f"Adding {desc} improves prediction of unseen perturbations.",
                         "rationale": why, "category": cat, "action": "new_feature", "parent": None,
                         "new_feature": {"name": name, "description": desc, "implementation_hint": desc,
                                         "params": {}}, "model_type": "ridge", "replicates": 1})
            self.cursor += 1
        if not hyps:
            # Greedy forward selection: add the best helpful feature not yet in the best model.
            missing = _section(research_state, "HELPFUL FEATURES MISSING FROM BEST")
            if missing:
                hyps.append({"title": f"Combine {missing[0]}", "category": "exploit", "action": "combine",
                             "hypothesis": f"Adding {missing[0]} to the current best model gives additive gains.",
                             "rationale": "It helped on its own relative to the baseline; signals may be complementary.",
                             "parent": None, "add_features": [missing[0]]})
            elif not self.swept:
                self.swept = True
                hyps.append({"title": "Regularisation sweep", "category": "exploit", "action": "sweep",
                             "hypothesis": "The optimal ridge penalty shifted after features were added.",
                             "rationale": "More features can change the bias-variance balance.", "parent": None,
                             "model_type": "ridge", "sweep": {"target": "alpha_grid",
                                                              "values": [[0.001, 0.01], [300.0, 1000.0, 3000.0]]}})
            elif not self.lasso:
                self.lasso = True
                hyps.append({"title": "Lasso selection", "category": "risky", "action": "combine",
                             "hypothesis": "A sparse lasso model on the best feature set generalises as well with fewer features.",
                             "rationale": "Sparsity aids interpretability and reveals which features carry signal.",
                             "parent": None, "model_type": "lasso", "add_features": []})
        text = json.dumps({"synthesis": "Scripted planner: fixed hypothesis list, then greedy combination.",
                           "hypotheses": hyps})
        return LLMResponse(text=text, usage=Usage(), provider=self.name, model=self.model)


class LoadTestPlanner(AgentProvider):
    """Planner for load tests: an endless stream of distinct feature hypotheses after a simulated delay.

    Lets the controller, workers, database, git isolation and executor be exercised at 8/16/44 workers
    without paying for LLM calls (pair it with MockProvider and latency_s/latency_jitter_s)."""
    name = "loadtest"

    def __init__(self, model: str = "loadtest", latency_s: float = 0.0, replicates: int = 1):
        super().__init__(model)
        self.latency_s = latency_s
        self.replicates = replicates
        self.counter = 0
        self._lock = threading.Lock()

    def complete(self, system: str, user: str, max_tokens: int) -> LLMResponse:
        return LLMResponse(text="{}", provider=self.name, model=self.model)

    def propose(self, research_state: str, n: int, mix: dict, max_tokens: int) -> LLMResponse:
        if self.latency_s:
            time.sleep(self.latency_s)
        hyps = []
        cats = ["explore"] * 13 + ["exploit"] * 5 + ["risky"] * 2
        for _ in range(n):
            with self._lock:
                self.counter += 1
                k = self.counter
            title, cat, name, desc, why = SCRIPTED_HYPOTHESES[(k - 1) % len(SCRIPTED_HYPOTHESES)]
            hyps.append({"title": f"{title} #{k}", "category": cats[k % len(cats)],
                         "hypothesis": f"Variant {k}: adding {desc} improves prediction.",
                         "rationale": why, "action": "new_feature", "parent": None,
                         "new_feature": {"name": f"{name}_v{k}", "description": desc,
                                         "implementation_hint": desc, "params": {}},
                         "model_type": "ridge", "replicates": self.replicates})
        text = json.dumps({"synthesis": "Load-test planner.", "hypotheses": hyps})
        return LLMResponse(text=text, usage=Usage(input_tokens=len(research_state) // 4,
                                                  output_tokens=len(text) // 4), provider=self.name,
                           model=self.model)


def _section(text: str, title: str) -> list[str]:
    lines, out, on = text.splitlines(), [], False
    for line in lines:
        if line.startswith("## "):
            on = line[3:].strip() == title
            continue
        if on and line.startswith("- ") and line[2:].strip() != "(none)":
            out.append(line[2:].strip())
    return out
