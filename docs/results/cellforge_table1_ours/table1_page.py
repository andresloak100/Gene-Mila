#!/usr/bin/env python3
"""Paper-style HTML of table.json beside CellForge rows. Run: python3 docs/results/cellforge_table1_ours/table1_page.py . out.html docs/results/cellforge_table1_ours/table1_template.html"""
import json, sys, html
from pathlib import Path
R = Path(sys.argv[1]); OUT = Path(sys.argv[2])
ours = json.loads((R/"docs/results/cellforge_table1_ours/table.json").read_text())["datasets"]
cf = json.loads((R/"docs/results/cellforge_table1.json").read_text())["datasets"]
COLS = ["cellforge_mse","cellforge_pcc","cellforge_r2","cellforge_mse_de","cellforge_pcc_de","cellforge_r2_de","pearson_delta"]
LOWER = {0, 3}
OURS_ROWS = [
 ("Unperturbed (control mean)", "Unperturbed (control mean)", False),
 ("Mean response (lab's start, OLS)", "Lab's starting model", False),
 ("Additive singles (lab's start)", "Lab's starting model", False),
 ("Linear, Ahlmann-Eltze 2025", "Linear (Ahlmann-Eltze 2025)", False),
 ("GEARS, Roohani 2023", "GEARS (Roohani 2023)", False),
 ("Gene-Mila agents, DeepSeek, clean tier 1 (block G0)", "Gene-Mila agents, run G0", True),
 ("Gene-Mila agents, DeepSeek, clean tier 1 + tables (G1)", "Gene-Mila agents + gene tables, run G1", True),
 ("Gene-Mila agents, DeepSeek, clean tier 1 (block T0, code d53edff)", "Gene-Mila agents, run T0", True),
 ("CellForge pipeline, run by us, DeepSeek v4-pro (block U, 1 of 3 runs finished)", "CellForge pipeline, run by us (1 of 3 runs finished)", False),
 ("CellForge pipeline, run by us, DeepSeek v4-pro (block U, 0 of 3 runs finished)", "CellForge pipeline, run by us (0 of 3 runs finished)", False),
]
def ranks(vals, j):
    xs = sorted({v for v in vals if v is not None}, reverse=(j not in LOWER))
    return (xs[0] if xs else None, xs[1] if len(xs) > 1 else None)
def cell(m, sd, best, second, n_dec=4):
    if m is None:
        return '<td class="pend">–</td>'
    cls = "best" if m == best else ("second" if m == second else "")
    s = f'<span class="v">{m:.{n_dec}f}</span>'
    if sd is not None:
        s += f'<span class="sd">±{sd:.4f}</span>'
    return f'<td class="{cls}">{s}</td>'
body = []
for ds in ("adamson", "norman", "srivatsan"):
    title = cf[ds]["title"]
    name, _, rest = title.partition("(")
    rows_html = []
    o = ours.get(ds, {})
    ourrows = []
    for key, label, mine in OURS_ROWS:
        if key not in o: continue
        r = o[key]; met = r["metrics"]
        ourrows.append((label, mine, r["n"], [None if not met else met[k]["mean"] for k in COLS], [None if not met else met[k]["sd"] for k in COLS]))
    cfrows = [(lab, [x[0] if isinstance(x, list) else x for x in v], cf[ds]["std"].get(lab)) for lab, v in cf[ds]["rows"].items()]
    n_rows = len(ourrows) + len(cfrows) + (1 if not ourrows else 0) + 2
    first = True
    def lead():
        global first
        if first:
            first = False
            short = name.strip().split(",")[0]
            return f'<th class="ds" rowspan="{n_rows}" scope="rowgroup"><span>{html.escape(title.split("(")[-1].rstrip(")"))}</span></th>'
        return ""
    rows_html.append(f'<tr class="sub">{lead()}<td colspan="8">Our split · scored once on the sealed held-out perturbations</td></tr>')
    if ourrows:
        bests = [ranks([r[3][j] for r in ourrows], j) for j in range(7)]
        for label, mine, n, ms, sds in ourrows:
            tds = "".join(cell(ms[j], sds[j], *bests[j]) for j in range(7))
            rows_html.append(f'<tr class="{"ours" if mine else ""}">{lead()}<th scope="row">{html.escape(label)}{f"<small>n = {n}</small>" if n and n > 1 else ""}</th>{tds}</tr>')
    else:
        rows_html.append(f'<tr class="none">{lead()}<td colspan="8">No row of ours. The lab models genetic perturbations, Srivatsan tests drugs, and no data bundle exists yet.</td></tr>')
    rows_html.append(f'<tr class="sub cfsub">{lead()}<td colspan="8">CellForge paper, Table 1 · own split, copied as published, not comparable</td></tr>')
    bests = [ranks([r[1][j] for r in cfrows], j) for j in range(6)]
    for lab, v, sd in cfrows:
        tds = "".join(cell(v[j], sd[j] if sd else None, *bests[j]) for j in range(6)) + '<td class="na">–</td>'
        rows_html.append(f'<tr class="cf">{lead()}<th scope="row">{html.escape(lab)}</th>{tds}</tr>')
    body.append(f'<tbody class="dsg">{"".join(rows_html)}</tbody>')
TPL = (Path(sys.argv[3])).read_text()
OUT.write_text(TPL.replace("{{BODY}}", "\n".join(body)))
print("ok", OUT)
