#!/usr/bin/env python3
"""Draw the README figures in docs/assets/ from the numbers in docs/.

    pip install fonttools
    python docs/assets/build_figures.py

Every figure is a self-contained SVG: lettering is converted to outlines from the OFL fonts in
docs/assets/fonts/ (so it looks the same on every machine and inside GitHub's <img> sandbox),
colours come from the tokens below, and an internal stylesheet switches to the dark palette
under prefers-color-scheme. Numbers are parsed from the run reports under docs/, never typed
in here, so a new run report means re-running this script, not editing an SVG. Design rules
are in docs/assets/DESIGN.md.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent

# ---------------------------------------------------------------- design tokens

LIGHT = {
    "paper": "#F7F5EF", "panel": "#EFECE3", "ink": "#1B2027", "soft": "#555E69",
    "faint": "#8A929B", "rule": "#D9D4C7", "grid": "#E6E1D5",
    "gain": "#0B7A6E", "clock": "#D4452A", "worker": "#B07415", "pi": "#3C4FA8",
    "base": "#9AA1A9",
}
DARK = {
    "paper": "#12171D", "panel": "#1A2028", "ink": "#E8EBEE", "soft": "#A9B1BA",
    "faint": "#77808A", "rule": "#2D343D", "grid": "#202730",
    "gain": "#3CC4B1", "clock": "#FF7A5C", "worker": "#E5B04E", "pi": "#93A3FF",
    "base": "#6E7781",
}

FONT_FILES = {
    "display": "fraunces-latin-600-normal.woff",
    "italic": "fraunces-latin-400-italic.woff",
    "sans": "ibm-plex-sans-latin-400-normal.woff",
    "sans-medium": "ibm-plex-sans-latin-500-normal.woff",
    "mono": "ibm-plex-mono-latin-400-normal.woff",
    "mono-medium": "ibm-plex-mono-latin-500-normal.woff",
}


def stylesheet() -> str:
    def rules(tokens: dict) -> str:
        out = []
        for name, colour in tokens.items():
            out.append(f".f-{name}{{fill:{colour}}}.s-{name}{{stroke:{colour}}}")
        return "".join(out)
    return (f"<style>{rules(LIGHT)}"
            f"@media (prefers-color-scheme: dark){{{rules(DARK)}}}</style>")


# ---------------------------------------------------------------- lettering

class Face:
    def __init__(self, key: str, path: Path):
        self.key = key
        self.font = TTFont(str(path))
        self.upm = self.font["head"].unitsPerEm
        self.cmap = self.font.getBestCmap()
        self.hmtx = self.font["hmtx"]
        self.glyphs = self.font.getGlyphSet()
        self.kern = self._pair_kerning()

    def _pair_kerning(self) -> dict[tuple[str, str], int]:
        pairs: dict[tuple[str, str], int] = {}
        if "GPOS" not in self.font:
            return pairs
        table = self.font["GPOS"].table
        for lookup in table.LookupList.Lookup:
            subtables = lookup.SubTable
            if lookup.LookupType == 9:
                subtables = [s.ExtSubTable for s in subtables if s.ExtensionLookupType == 2]
            elif lookup.LookupType != 2:
                continue
            for st in subtables:
                cov = st.Coverage.glyphs
                if st.Format == 1:
                    for first, pset in zip(cov, st.PairSet):
                        for rec in pset.PairValueRecord:
                            v = getattr(rec.Value1, "XAdvance", 0) or 0
                            if v:
                                pairs.setdefault((first, rec.SecondGlyph), v)
                elif st.Format == 2:
                    c1 = st.ClassDef1.classDefs if st.ClassDef1 else {}
                    c2 = st.ClassDef2.classDefs
                    seconds: dict[int, list[str]] = {}
                    for g, c in c2.items():
                        seconds.setdefault(c, []).append(g)
                    for first in cov:
                        row = st.Class1Record[c1.get(first, 0)]
                        for c, rec in enumerate(row.Class2Record):
                            v = getattr(rec.Value1, "XAdvance", 0) or 0
                            if v:
                                for second in seconds.get(c, []):
                                    pairs.setdefault((first, second), v)
        return pairs

    def glyph_name(self, ch: str) -> str:
        return self.cmap.get(ord(ch)) or self.cmap.get(ord("?"))

    def advance(self, name: str) -> int:
        return self.hmtx[name][0]

    def outline(self, name: str) -> str:
        pen = SVGPathPen(self.glyphs)
        self.glyphs[name].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
        d = pen.getCommands()
        return re.sub(r"(\d+\.\d{1})\d+", r"\1", d)


_FACES: dict[str, Face] = {}


def face(key: str) -> Face:
    if key not in _FACES:
        _FACES[key] = Face(key, HERE / "fonts" / FONT_FILES[key])
    return _FACES[key]


class Canvas:
    """An SVG under construction: glyph outlines are defined once and reused with <use>."""

    def __init__(self, width: int, height: int, title: str, desc: str, source: str):
        self.w, self.h = width, height
        self.title, self.desc, self.source = title, desc, source
        self.defs: dict[str, str] = {}
        self.body: list[str] = []

    def add(self, fragment: str) -> None:
        self.body.append(fragment)

    def measure(self, text: str, size: float, font: str = "sans", tracking: float = 0) -> float:
        f = face(font)
        names = [f.glyph_name(c) for c in text]
        units = sum(f.advance(n) for n in names)
        units += sum(f.kern.get((a, b), 0) for a, b in zip(names, names[1:]))
        return units * size / f.upm + tracking * size * max(len(text) - 1, 0)

    def text(self, text: str, x: float, y: float, size: float, font: str = "sans",
             colour: str = "ink", anchor: str = "start", tracking: float = 0) -> float:
        """Set `text` with its baseline at y. Returns the advance width in px."""
        f = face(font)
        width = self.measure(text, size, font, tracking)
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        scale = size / f.upm
        names = [f.glyph_name(c) for c in text]
        pen_x, uses = 0.0, []
        for i, name in enumerate(names):
            if text[i] != " ":
                gid = f"{f.key[0]}{f.key[-1]}{f.font.getGlyphID(name)}"
                if gid not in self.defs:
                    self.defs[gid] = f'<path id="{gid}" d="{f.outline(name)}"/>'
                uses.append(f'<use href="#{gid}" x="{pen_x:.0f}"/>')
            pen_x += f.advance(name)
            if i + 1 < len(names):
                pen_x += f.kern.get((name, names[i + 1]), 0) + tracking * f.upm
        self.add(f'<g class="f-{colour}" transform="translate({x:.1f} {y:.1f}) scale({scale:.5f})">'
                 + "".join(uses) + "</g>")
        return width

    def svg(self) -> str:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" role="img">\n'
                f"<title>{html.escape(self.title)}</title>\n<desc>{html.escape(self.desc)}</desc>\n"
                f"<!-- Generated by docs/assets/build_figures.py from {self.source}. Do not edit by hand. -->\n"
                f"{stylesheet()}\n<defs>{''.join(self.defs.values())}</defs>\n"
                + "\n".join(self.body) + "\n</svg>\n")

    def save(self, name: str) -> Path:
        path = HERE / name
        path.write_text(self.svg())
        return path


# ---------------------------------------------------------------- data from docs/

def example_run() -> dict:
    """Numbers for the example run, parsed from docs/example_run/*.md and the planner state."""
    run_dir = DOCS / "example_run"
    summary = (run_dir / "summary.md").read_text()
    analysis = (run_dir / "analysis.md").read_text()
    state = (run_dir / "research_state_round3.txt").read_text()

    experiments = []
    for row in re.finditer(r"^\| (EXP_\d+) \| (W\d+) \| (\w+) \| ([^|]*) \| ([\d.]*) \| ([^|]*) \| (\d+) \|",
                           analysis, re.M):
        exp, worker, status, what, score, delta, calls = (g.strip() for g in row.groups())
        experiments.append({
            "id": exp, "worker": worker, "status": status, "what": what,
            "score": float(score) if score else None, "llm_calls": int(calls),
            "kind": "feature" if int(calls) > 0 else "config",
        })

    baselines = []
    for m in re.finditer(r'"id": "(EXP_\d+)", "what": "([^"]+)", "score": ([\d.]+)', state):
        baselines.append({"id": m.group(1), "what": m.group(2).rstrip("\\u2026…").strip(),
                          "score": float(m.group(3))})

    lineage = [{"id": m.group(1), "label": m.group(2), "score": float(m.group(3))}
               for m in re.finditer(r"(EXP_\d+) \[([^\]]+)\] score ([\d.]+)", summary)]
    query_only = {m.group(1): (float(m.group(2)), float(m.group(3)))
                  for m in re.finditer(r"^\| (EXP_\d+) \| \w+ \| ([\d.]+) \| ([\d.]+) \|", summary, re.M)}
    coefficients = [(m.group(1), float(m.group(2)))
                    for m in re.finditer(r"^- (\S+): coefficient ([+-][\d.]+)", summary, re.M)]
    failed = [{"id": m.group(1), "feature": m.group(2), "reason": m.group(3)}
              for m in re.finditer(r"^- (EXP_\d+) (\S+) \[\w+\]: (.+)$", summary, re.M)]
    minutes = float(re.search(r"Duration: ([\d.]+) min", summary).group(1))
    completed = int(re.search(r"Experiments completed: (\d+)", summary).group(1))
    return {"experiments": experiments, "baselines": baselines, "lineage": lineage,
            "query_only": query_only, "coefficients": coefficients, "failed": failed,
            "minutes": minutes, "completed": completed}


# ---------------------------------------------------------------- figures

def plate(c: Canvas, inset: float = 0) -> None:
    c.add(f'<rect class="f-paper s-rule" x="{inset + .5}" y="{inset + .5}" width="{c.w - 2 * inset - 1}" '
          f'height="{c.h - 2 * inset - 1}" rx="16" stroke-width="1"/>')


def kicker(c: Canvas, text: str, x: float, y: float, colour: str = "soft") -> float:
    return c.text(text.upper(), x, y, 11.5, "mono-medium", colour, tracking=0.08)


def fmt(v: float, places: int = 4) -> str:
    return f"{v:.{places}f}"


def example_run_figure() -> Path:
    run = example_run()
    exps = run["experiments"]
    base = next(b for b in run["baselines"] if b["id"] == "EXP_0004")["score"]
    steps = run["lineage"][1:]
    best_id = run["lineage"][-1]["id"]
    best = run["lineage"][-1]["score"]
    visible, sealed = run["query_only"][best_id]
    base_sealed = run["query_only"]["EXP_0004"][1]
    rejected = [e for e in exps if e["score"] is None]

    c = Canvas(960, 540, "Every experiment of the synthetic example run",
               f"{len(exps)} experiments after the baselines, {run['minutes']} minutes, synthetic knockout screen. "
               f"Worker-written features and Python sweeps are plotted by pearson_delta on visible validation "
               f"against the linear baseline at {fmt(base)}. The winning lineage adds one feature per step and "
               f"reaches {fmt(best)}; on the sealed query-only set it scores {fmt(sealed)} against {fmt(base_sealed)} "
               f"for the baseline. {len(rejected)} feature was rejected by the label-leakage test.",
               "docs/example_run/analysis.md and docs/example_run/summary.md")
    plate(c)
    x0, x1, y0, y1 = 76, 690, 168, 438          # plot box
    lo, hi = 0.58, 0.80

    def sy(v: float) -> float:
        return y1 - (v - lo) / (hi - lo) * (y1 - y0)

    def sx(i: int) -> float:
        return x0 + 16 + i * (x1 - x0 - 32) / (len(exps) - 1)

    kicker(c, f"Example run  /  synthetic knockout screen  /  4 workers  /  {run['minutes']} min", 40, 54)
    c.text("Agents propose features. The numbers decide which stay.", 40, 94, 25, "display")
    c.text(f"{len(exps)} experiments after the baselines, in queue order, scored by pearson_delta on visible validation.",
           40, 124, 14, "sans", "soft")

    for v in (0.60, 0.65, 0.70, 0.75, 0.80):
        y = sy(v)
        c.add(f'<line class="s-grid" x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}" stroke-width="1"/>')
        c.text(f"{v:.2f}", x0 - 12, y + 4, 11, "mono", "faint", anchor="end")
    yb = sy(base)
    c.add(f'<line class="s-base" x1="{x0}" x2="{x1}" y1="{yb:.1f}" y2="{yb:.1f}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    c.text(f"linear baseline {fmt(base)}", x1, yb + 18, 11.5, "mono", "faint", anchor="end")

    # best so far, starting from the baseline
    d, running = [f"M{x0} {yb:.1f}"], base
    for i, e in enumerate(exps):
        if e["score"] is not None and e["score"] > running:
            running = e["score"]
            d.append(f"H{sx(i):.1f}V{sy(running):.1f}")
    d.append(f"H{x1}")
    c.add(f'<path class="s-gain" fill="none" stroke-width="2.25" stroke-linejoin="round" d="{"".join(d)}"/>')

    for i, e in enumerate(exps):
        x = sx(i)
        if e["score"] is None:
            y = y1 + 30
            c.add(f'<path class="s-clock" stroke-width="2.4" stroke-linecap="round" '
                  f'd="M{x - 5:.1f} {y - 5:.1f}L{x + 5:.1f} {y + 5:.1f}M{x + 5:.1f} {y - 5:.1f}L{x - 5:.1f} {y + 5:.1f}"/>')
            c.text(f"{e['id']} rejected: its feature leaked the label", x + 14, y + 4.5, 11.5, "mono", "clock")
        elif e["kind"] == "feature":
            c.add(f'<circle class="f-worker s-paper" cx="{x:.1f}" cy="{sy(e["score"]):.1f}" r="5.5" stroke-width="1.5"/>')
        else:
            c.add(f'<circle class="f-paper s-soft" cx="{x:.1f}" cy="{sy(e["score"]):.1f}" r="3.6" stroke-width="1.3"/>')

    # winning lineage: numbered markers on the plot, key in the empty middle of the plot
    index = {e["id"]: i for i, e in enumerate(exps)}
    kx, ky = 318, sy(0.745) + 26
    c.add(f'<rect class="f-panel" x="{kx - 16}" y="{ky - 26}" width="352" height="{30 + 24 * len(steps)}" rx="8"/>')
    kicker(c, "Winning lineage, one feature per step", kx, ky - 6, "gain")
    for n, step in enumerate(steps, 1):
        i = index[step["id"]]
        x, y = sx(i), sy(step["score"])
        my = y - 19
        c.add(f'<line class="s-gain" x1="{x:.1f}" x2="{x:.1f}" y1="{my + 7:.1f}" y2="{y - 6:.1f}" stroke-width="1.2"/>')
        c.add(f'<circle class="f-gain" cx="{x:.1f}" cy="{my:.1f}" r="8"/>')
        c.text(str(n), x, my + 4.2, 11.5, "mono-medium", "paper", anchor="middle")
        row = ky + 20 + 24 * (n - 1)
        c.add(f'<circle class="f-gain" cx="{kx + 7}" cy="{row - 4.5:.1f}" r="7.5"/>')
        c.text(str(n), kx + 7, row - 0.4, 11, "mono-medium", "paper", anchor="middle")
        c.text("+ " + re.sub(r"_e\d+$", "", step["label"]), kx + 24, row, 12.5, "mono", "ink")
        c.text(fmt(step["score"]), kx + 318, row, 12.5, "mono-medium", "gain", anchor="end")

    # sealed set
    px, pw = 724, 200
    c.add(f'<rect class="f-panel" x="{px}" y="{y0 - 10}" width="{pw}" height="{y1 - y0 + 20}" rx="10"/>')
    kicker(c, "Sealed set", px + 20, y0 + 18, "ink")
    c.text("query-only validation,", px + 20, y0 + 40, 12.5, "sans", "soft")
    c.text("opened once at the end", px + 20, y0 + 57, 12.5, "sans", "soft")
    c.text("best model", px + 20, y0 + 100, 12.5, "sans", "soft")
    c.text(fmt(sealed), px + 20, y0 + 134, 32, "display", "gain")
    c.text(f"visible {fmt(visible)}", px + 20, y0 + 156, 11.5, "mono", "faint")
    c.text("linear baseline", px + 20, y0 + 198, 12.5, "sans", "soft")
    c.text(fmt(base_sealed), px + 20, y0 + 232, 32, "display", "base")
    c.text(f"visible {fmt(base)}", px + 20, y0 + 254, 11.5, "mono", "faint")

    ly = 508
    c.add(f'<circle class="f-worker" cx="46" cy="{ly - 4}" r="5.5"/>')
    lx = 58 + c.text("feature written by a worker LLM", 58, ly, 12, "sans", "soft")
    c.add(f'<circle class="f-paper s-soft" cx="{lx + 24}" cy="{ly - 4}" r="3.6" stroke-width="1.3"/>')
    lx = lx + 34 + c.text("sweep generated in Python, no LLM call", lx + 34, ly, 12, "sans", "soft")
    c.add(f'<path class="s-gain" stroke-width="2.25" d="M{lx + 22} {ly - 4}h18"/>')
    c.text("best so far", lx + 46, ly, 12, "sans", "soft")
    c.text("synthetic data  /  docs/example_run/", c.w - 36, ly, 11.5, "mono", "faint", anchor="end")
    return c.save("example-run.svg")


def wrap(c: Canvas, text: str, width: float, size: float, font: str = "sans") -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and c.measure(trial, size, font) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + ([line] if line else [])


def arrow(c: Canvas, d: str, colour: str = "soft", dashed: bool = False, width: float = 1.6) -> None:
    dash = ' stroke-dasharray="4 4"' if dashed else ""
    c.add(f'<path class="s-{colour}" fill="none" stroke-width="{width}" stroke-linecap="round" '
          f'stroke-linejoin="round"{dash} d="{d}"/>')


def head(c: Canvas, x: float, y: float, direction: str, colour: str = "soft") -> None:
    pts = {"right": (-7, -4.5, -7, 4.5), "left": (7, -4.5, 7, 4.5),
           "down": (-4.5, -7, 4.5, -7), "up": (-4.5, 7, 4.5, 7)}[direction]
    c.add(f'<path class="f-{colour}" d="M{x} {y}L{x + pts[0]} {y + pts[1]}L{x + pts[2]} {y + pts[3]}Z"/>')


def station(c: Canvas, x: float, y: float, w: float, h: float, role: str, name: str, detail: str,
            colour: str) -> None:
    c.add(f'<rect class="f-paper s-rule" x="{x}" y="{y}" width="{w}" height="{h}" rx="10" stroke-width="1.2"/>')
    c.add(f'<rect class="f-{colour}" x="{x}" y="{y + 14}" width="3.5" height="{h - 28}" rx="1.75"/>')
    kicker(c, role, x + 16, y + 26, colour)
    c.text(name, x + 16, y + 49, 15, "sans-medium", "ink")
    for i, line in enumerate(wrap(c, detail, w - 30, 12.5)):
        c.text(line, x + 16, y + 72 + i * 17, 12.5, "sans", "soft")


def loop_figure() -> Path:
    c = Canvas(960, 520, "How one experiment moves through the lab",
               "Claude, as planner, proposes hypotheses. The Python controller queues them and adds sweeps and "
               "replicates. A worker LLM in its own git worktree writes one feature plugin. Guards check the code "
               "(AST rules, smoke and label-leakage test, diff limited to one file). A ridge, lasso, elastic net or "
               "OLS model is fitted on CPU in a limited subprocess. The controller scores it on visible validation "
               "and records it in the research memory the planner reads next. All of this runs inside the deadline; "
               "after it, the top candidates are scored once on the sealed query-only set.",
               "genemila/ (controller.py, planner.py, worker.py, guard.py, pipeline.py, report.py)")
    plate(c)
    kicker(c, "One experiment, end to end", 40, 54)
    c.text("LLMs propose and write code. Python fits, scores and keeps time.", 40, 94, 25, "display")

    fx0, fy0, fx1, fy1 = 40, 128, 716, 486
    c.add(f'<rect class="s-clock" fill="none" x="{fx0}" y="{fy0}" width="{fx1 - fx0}" height="{fy1 - fy0}" '
          f'rx="14" stroke-width="1.5" stroke-dasharray="7 5"/>')
    tag = "Inside the deadline"
    tw = c.measure(tag.upper(), 11.5, "mono-medium", 0.08)
    c.add(f'<rect class="f-paper" x="{fx0 + 18}" y="{fy0 - 9}" width="{tw + 50}" height="18"/>')
    c.add(f'<circle class="s-clock" fill="none" cx="{fx0 + 33}" cy="{fy0}" r="7" stroke-width="1.5"/>')
    c.add(f'<path class="s-clock" fill="none" stroke-width="1.5" stroke-linecap="round" d="M{fx0 + 33} {fy0 - 4}V{fy0}L{fx0 + 36} {fy0 + 2}"/>')
    kicker(c, tag, fx0 + 48, fy0 + 4, "clock")

    w, h, gap = 148, 128, 18
    xs = [fx0 + 20 + i * (w + gap) for i in range(4)]
    top, bottom = fy0 + 30, fy0 + 30 + h + 56
    station(c, xs[0], top, w, h, "Claude", "Planner", "reads the research memory, proposes hypotheses as JSON", "pi")
    station(c, xs[1], top, w, h, "Python", "Controller", "queues them and adds sweeps and replicates", "ink")
    station(c, xs[2], top, w, h, "Worker LLM", "One feature", "writes a single plugin file in its own git worktree", "worker")
    station(c, xs[3], top, w, h, "Python", "Guards", "AST rules, smoke and leakage test, diff limited to that file", "clock")
    station(c, xs[3], bottom, w, h, "CPU", "Linear fit", "ridge, lasso, elastic net or OLS in a limited subprocess", "ink")
    station(c, xs[2], bottom, w, h, "Python", "Score", "pearson_delta on visible validation, by the controller", "gain")
    station(c, xs[1], bottom, w, h, "SQLite", "Research memory", "every result and failure, compressed for the planner", "ink")

    mid = top + h / 2
    for i in range(3):
        arrow(c, f"M{xs[i] + w + 3} {mid}H{xs[i + 1] - 4}")
        head(c, xs[i + 1] - 3, mid, "right")
    cx = xs[3] + w / 2
    arrow(c, f"M{cx} {top + h + 3}V{bottom - 4}")
    head(c, cx, bottom - 3, "down")
    bm = bottom + h / 2
    for i in (3, 2):
        arrow(c, f"M{xs[i] - 3} {bm}H{xs[i - 1] + w + 4}")
        head(c, xs[i - 1] + w + 3, bm, "left")
    # memory back to planner
    px = xs[0] + w / 2
    arrow(c, f"M{xs[1] - 3} {bm}H{px + 10}Q{px} {bm} {px} {bm - 10}V{top + h + 4}", "pi")
    head(c, px, top + h + 3, "up", "pi")
    c.text("next round", px + 8, top + h + 30, 11.5, "mono", "pi")
    # what happens when a guard fails
    gy = top + h + 32
    c.text("passes", cx + 9, gy - 2, 11, "mono", "soft")
    c.text("fails: error sent back for a fix, then recorded as rejected", cx - 12, gy + 14, 11, "mono",
           "clock", anchor="end")

    # after the deadline
    sx0 = 742
    c.add(f'<rect class="f-panel" x="{sx0}" y="{fy0}" width="{c.w - 40 - sx0}" height="{fy1 - fy0}" rx="14"/>')
    kicker(c, "After the deadline", sx0 + 20, fy0 + 30, "ink")
    lines = [("Stop", "no new work; running fits get 30 s, then are killed"),
             ("Sealed set", "top candidates scored once on query-only validation"),
             ("cell-eval", "finalists scored with Arc's cell-eval on real data"),
             ("Watchdog", "kills the whole process group if anything overruns")]
    y = fy0 + 64
    for name, detail in lines:
        c.text(name, sx0 + 20, y, 14, "sans-medium", "ink")
        for j, line in enumerate(wrap(c, detail, c.w - 40 - sx0 - 40, 12)):
            c.text(line, sx0 + 20, y + 19 + j * 16, 12, "sans", "soft")
        y += 19 + 16 * len(wrap(c, detail, c.w - 40 - sx0 - 40, 12)) + 20
    return c.save("loop.svg")


def hero_figure() -> Path:
    run = example_run()
    readme = (DOCS / "example_run" / "README.md").read_text()
    budget = int(re.search(r"--minutes (\d+)", readme).group(1))
    planner = re.search(r"--planner-model (\w+)", readme).group(1).capitalize()
    worker = re.search(r"--worker-model (\w+)", readme).group(1).capitalize()
    base = next(b for b in run["baselines"] if b["id"] == "EXP_0004")["score"]
    best_id, best = run["lineage"][-1]["id"], run["lineage"][-1]["score"]
    sealed = run["query_only"][best_id][1]
    rejected = sum(1 for e in run["experiments"] if e["score"] is None)

    c = Canvas(960, 300, "Gene-Mila",
               "Gene-Mila: an autonomous research lab for single-cell perturbation prediction. Agents write the "
               "features, only a linear model may use them, and the clock stops everyone. Example run on synthetic "
               f"data: {budget}-minute budget, {run['minutes']} minutes used, {len(run['experiments'])} experiments, "
               f"best model {fmt(best)} pearson_delta against a {fmt(base)} baseline, {fmt(sealed)} on the sealed set.",
               "docs/example_run/README.md and docs/example_run/summary.md")
    plate(c)
    kicker(c, "Autonomous lab  /  single-cell perturbation prediction", 44, 62)
    c.text("Gene-Mila", 40, 146, 80, "display")
    c.text("Agents write the features.", 44, 196, 21, "italic", "soft")
    c.text("Only a linear model may use them.", 44, 224, 21, "italic", "soft")
    c.text("The clock stops everyone.", 44, 252, 21, "italic", "clock")

    # run card
    x, y, w = 586, 40, 334
    c.add(f'<rect class="f-panel" x="{x}" y="{y}" width="{w}" height="220" rx="12"/>')
    kicker(c, "Example run", x + 22, y + 32, "ink")
    c.text("synthetic", x + w - 22, y + 32, 11.5, "mono-medium", "clock", anchor="end")
    rows = [
        ("models", f"Claude {planner} / {worker}", "ink"),
        ("budget", f"{budget} min, used {run['minutes']}", "ink"),
        ("experiments", f"{len(run['experiments'])}, {rejected} rejected", "ink"),
        ("linear baseline", fmt(base), "base"),
        ("best model", fmt(best), "gain"),
        ("sealed set", fmt(sealed), "gain"),
    ]
    for i, (label, value, colour) in enumerate(rows):
        ry = y + 66 + i * 26
        lw = c.text(label, x + 22, ry, 12.5, "mono", "soft")
        vw = c.measure(value, 12.5, "mono-medium")
        dots_from, dots_to = x + 22 + lw + 8, x + w - 22 - vw - 8
        c.add(f'<line class="s-rule" x1="{dots_from:.1f}" x2="{dots_to:.1f}" y1="{ry - 3.5}" y2="{ry - 3.5}" '
              f'stroke-width="1.4" stroke-dasharray="1 4" stroke-linecap="round"/>')
        c.text(value, x + w - 22, ry, 12.5, "mono-medium", colour, anchor="end")
    return c.save("hero.svg")


def social_preview_figure() -> Path:
    """1280x640 card for the repository's social preview (Settings > Social preview).
    Render it to social-preview.png with any browser at that size."""
    c = Canvas(1280, 640, "Gene-Mila",
               "Gene-Mila: agents write the features, only a linear model may use them, the clock stops everyone. "
               "An autonomous lab for single-cell perturbation prediction.", "the README tagline")
    c.add(f'<rect class="f-paper" width="{c.w}" height="{c.h}"/>')
    c.add(f'<rect class="f-clock" x="0" y="0" width="{c.w}" height="10"/>')
    kicker_size = 17
    c.text("AUTONOMOUS LAB  /  SINGLE-CELL PERTURBATION PREDICTION", 92, 150, kicker_size, "mono-medium", "soft",
           tracking=0.08)
    c.text("Gene-Mila", 84, 318, 168, "display")
    c.text("Agents write the features.", 94, 410, 38, "italic", "soft")
    c.text("Only a linear model may use them.", 94, 462, 38, "italic", "soft")
    c.text("The clock stops everyone.", 94, 514, 38, "italic", "clock")
    c.text("ridge  /  lasso  /  elastic net  /  OLS", c.w - 92, 580, 17, "mono", "faint", anchor="end")
    return c.save("social-preview.svg")


if __name__ == "__main__":
    for build in (hero_figure, example_run_figure, loop_figure, social_preview_figure):
        print(build().relative_to(DOCS.parent))
