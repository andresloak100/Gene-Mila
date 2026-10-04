#!/usr/bin/env python3
"""Deterministic checks on the repository's public face: README.md, docs/assets/ and the
GitHub About profile in .github/repo-profile.toml.

    python tools/readme_check.py               # report problems, exit 1 if any error
    python tools/readme_check.py --gh-command # print the `gh repo edit` command for the About box
    python tools/readme_check.py --hook       # Claude Code PostToolUse hook mode (reads JSON on stdin)

Judgement calls (is the page generic? does the first screen say something only this project
could say?) belong to the readme-designer agent (.claude/agents/readme-designer.md). Everything
that can be decided mechanically is decided here, so the agent and CI agree on it:

* every relative link, image and anchor resolves, and every image has alt text
* nothing GitHub's sanitizer strips (style attributes, <style>, <script>, event handlers)
* no stock marketing phrases, emoji-led headings or bullets, badge walls, or test counts
* every command in a shell block or inline code names a real script, real flags and real
  config keys, and every inline `section.key` that names a config section exists
* every score-like number (three or more decimals) traces to a file under docs/, and every
  README section or figure that shows one says the data is synthetic until real-data results
  exist (repo-profile: readme.results_label)
* SVG figures are self-contained (viewBox, <title>, no scripts or remote resources), and the
  numbers they draw (kept in each text group's aria-label) trace to docs/ like the README's
* the About description and topics fit GitHub's limits; the social preview is 2:1
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import struct
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11: the checks need tomllib, see main()
    tomllib = None

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / ".github" / "repo-profile.toml"

DEFAULT_BANNED = [
    "powerful", "seamless", "seamlessly", "cutting-edge", "cutting edge", "state-of-the-art",
    "state of the art", "leverage", "leverages", "leveraging", "revolutionize", "revolutionizes",
    "revolutionary", "unlock", "unlocks", "harness the power",
    "game-changing", "game changer", "blazing", "blazingly", "effortless", "effortlessly",
    "world-class", "best-in-class", "supercharge", "empower", "empowers", "robust and scalable",
    "easy to use", "easy-to-use", "simply put", "in today's", "dive into", "delve",
]
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF⭐⬆↔-↪]")
SCORE = re.compile(r"(?<![\w.$])0\.\d{3,4}(?!\d)")
REPO_PATH = re.compile(r"^(?:genemila|docs|configs|tests|tools|\.github|\.claude)/[\w./-]+$|^[\w-]+\.py$")


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def load_profile() -> dict:
    if not PROFILE.exists():
        return {}
    with PROFILE.open("rb") as fh:
        return tomllib.load(fh)


# ---------------------------------------------------------------- markdown helpers

def split_code(md: str) -> tuple[str, list[tuple[str, str, int]]]:
    """Return the markdown with fenced code blanked out, and the code blocks (lang, body, line)."""
    out, blocks, buf, lang, start, fence = [], [], [], "", 0, None
    for i, line in enumerate(md.splitlines(), 1):
        m = re.match(r"^\s*(`{3,}|~{3,})\s*([\w+-]*)", line)
        if fence is None and m:
            fence, lang, start, buf = m.group(1), m.group(2), i, []
            out.append("")
        elif fence is not None and line.strip().startswith(fence):
            blocks.append((lang, "\n".join(buf), start))
            fence = None
            out.append("")
        elif fence is not None:
            buf.append(line)
            out.append("")
        else:
            out.append(line)
    return "\n".join(out), blocks


def strip_inline_code(text: str) -> str:
    return re.sub(r"`[^`\n]*`", "", text)


def slugify(heading: str) -> str:
    # HTML tags are dropped only outside code spans: GitHub keeps `runs/<id>/` as text
    parts = heading.split("`")
    text = "".join(part if i % 2 else re.sub(r"<[^>]+>", "", part) for i, part in enumerate(parts))
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def heading_slugs(prose: str) -> set[str]:
    seen: dict[str, int] = {}
    slugs = set()
    for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*\s*$", prose, re.M):
        base = slugify(m.group(1))
        n = seen.get(base, 0)
        slugs.add(base if n == 0 else f"{base}-{n}")
        seen[base] = n + 1
    for m in re.finditer(r'<a\s+[^>]*(?:name|id)="([^"]+)"', prose):
        slugs.add(m.group(1))
    return slugs


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def docs_numbers() -> set[str]:
    nums: set[str] = set()
    for p in (ROOT / "docs").rglob("*"):
        if p.is_file() and "assets" not in p.parts and p.suffix in {".md", ".txt", ".json", ".py"}:
            nums.update(re.findall(r"\d+\.\d{3,}", p.read_text(errors="ignore")))
    return nums


def traceable(num: str, known: set[str]) -> bool:
    if num in known:
        return True
    places = len(num.split(".")[1])
    quantum = Decimal(1).scaleb(-places)
    return any(Decimal(k).quantize(quantum, ROUND_HALF_UP) == Decimal(num) for k in known
               if len(k.split(".")[1]) > places)


# ---------------------------------------------------------------- README checks

def check_links(name: str, md: str, prose: str, base: Path, rep: Report) -> list[str]:
    slugs = heading_slugs(prose)
    targets: list[tuple[str, int, str]] = []
    for m in re.finditer(r"(!?)\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)", prose):
        kind = "image" if m.group(1) else "link"
        if kind == "image" and not m.group(2).strip():
            rep.error(f"{name}:{line_of(prose, m.start())}", f"image {m.group(3)} has no alt text")
        targets.append((m.group(3), line_of(prose, m.start()), kind))
    for m in re.finditer(r"<img\b[^>]*>", prose, re.I):
        tag = m.group(0)
        src = re.search(r'\bsrc="([^"]+)"', tag)
        if not re.search(r'\balt="[^"]+"', tag):
            rep.error(f"{name}:{line_of(prose, m.start())}", "<img> has no alt text")
        if src:
            targets.append((src.group(1), line_of(prose, m.start()), "image"))
    for m in re.finditer(r'<source\b[^>]*\bsrcset="([^"]+)"', prose, re.I):
        targets.append((m.group(1).split()[0], line_of(prose, m.start()), "image"))
    for m in re.finditer(r'<a\b[^>]*\bhref="([^"]+)"', prose, re.I):
        targets.append((m.group(1), line_of(prose, m.start()), "link"))

    images = []
    for target, line, kind in targets:
        if re.match(r"^(?:[a-z][a-z0-9+.-]*:|//)", target, re.I):
            continue
        path, _, anchor = target.partition("#")
        path = path.split("?")[0]
        if not path:
            if anchor and anchor.lower() not in slugs:
                rep.error(f"{name}:{line}", f"anchor #{anchor} matches no heading")
            continue
        resolved = (base / path).resolve()
        if not resolved.exists():
            rep.error(f"{name}:{line}", f"{kind} target {path} does not exist")
        elif kind == "image":
            images.append(str(resolved.relative_to(ROOT)))
    return images


def check_sanitizer(name: str, prose: str, rep: Report) -> None:
    for pat, why in [(r"\sstyle\s*=", "style attributes are stripped by GitHub"),
                     (r"<style\b", "<style> is stripped by GitHub"),
                     (r"<script\b", "<script> is stripped by GitHub"),
                     (r"\son[a-z]+\s*=", "event handlers are stripped by GitHub")]:
        for m in re.finditer(pat, prose, re.I):
            rep.error(f"{name}:{line_of(prose, m.start())}", why)


def check_voice(name: str, prose: str, banned: list[str], max_badges: int, rep: Report) -> None:
    text = strip_inline_code(re.sub(r"<[^>]+>", " ", prose))
    for phrase in banned:
        for m in re.finditer(rf"(?<![\w-]){re.escape(phrase)}(?![\w-])", text, re.I):
            rep.error(f"{name}:{line_of(text, m.start())}", f'stock phrase "{m.group(0)}"; say the specific thing instead')
    for m in re.finditer(r"^[ \t]*(?:#{1,6}|[-*+]|\d+\.)[ \t]+(\S)", prose, re.M):
        if EMOJI.match(m.group(1)):
            rep.error(f"{name}:{line_of(prose, m.start())}", "heading or list item starts with an emoji")
    badges = len(re.findall(r"shields\.io|badgen\.net|/badge(?:\.svg)?\b", prose))
    if badges > max_badges:
        rep.error(name, f"{badges} badges (max {max_badges}); a badge wall reads as template")


def config_has(cfg: dict, dotted: str) -> bool:
    if set(dotted.split(".")) <= {"section", "key"}:  # the placeholder in `--set section.key=value`
        return True
    node = cfg
    for part in dotted.split("."):
        if not isinstance(node, dict) or part.strip('"') not in node:
            return False
        node = node[part.strip('"')]
    return True


def load_config() -> dict:
    with (ROOT / "configs" / "default.toml").open("rb") as fh:
        return tomllib.load(fh)


def defines_flag(src: str, flag: str) -> bool:
    return f'"{flag}"' in src or f"'{flag}'" in src


def script_source(script: Path) -> str:
    src = script.read_text()
    if "add_run_arg" in src:
        src += (ROOT / "genemila" / "cli_common.py").read_text()
    return src


def check_command(where: str, line: str, cfg: dict, rep: Report) -> None:
    """One `python script.py --flag ... --set key=value` line."""
    m = re.match(r"^python3?\s+(?!-m\b)(\S+\.py)\b(.*)$", line)
    if not m:
        return
    script = ROOT / m.group(1)
    if not script.exists():
        rep.error(where, f"command names {m.group(1)}, which does not exist")
        return
    src = script_source(script)
    try:
        tokens = shlex.split(m.group(2))
    except ValueError:
        tokens = m.group(2).split()
    for i, tok in enumerate(tokens):
        flag = tok.split("=")[0]
        if flag.startswith("--") and not defines_flag(src, flag):
            rep.error(where, f"{m.group(1)} has no {flag} option")
        if flag == "--set":
            value = tok.partition("=")[2] if "=" in tok else (tokens[i + 1] if i + 1 < len(tokens) else "")
            key = value.split("=")[0]
            if key and not config_has(cfg, key):
                rep.error(where, f"--set {key}: no such key in configs/default.toml")


def check_commands(name: str, blocks: list[tuple[str, str, int]], rep: Report) -> None:
    cfg = load_config()
    for lang, body, start in blocks:
        if lang not in {"bash", "sh", "shell", "console", "zsh", ""}:
            continue
        joined = re.sub(r"\\\n\s*", " ", body)
        for offset, raw in enumerate(joined.splitlines()):
            line = raw.split(" #")[0].strip().lstrip("$ ")
            check_command(f"{name}:{start + 1 + offset}", line, cfg, rep)


def check_inline_code(name: str, prose: str, rep: Report) -> None:
    """Commands, flags and config keys quoted in running text are held to the same standard."""
    cfg = load_config()
    scripts = "".join(p.read_text() for p in ROOT.glob("*.py")) + (ROOT / "genemila" / "cli_common.py").read_text()
    for m in re.finditer(r"`([^`\n]+)`", prose):
        span, where = m.group(1).strip(), f"{name}:{line_of(prose, m.start())}"
        if span.startswith(("python ", "python3 ")):
            check_command(where, span, cfg, rep)
            continue
        flag = re.match(r"^(--[a-z][\w-]*)(?:[ =](\S+))?", span)
        if flag:
            if not defines_flag(scripts, flag.group(1)):
                rep.error(where, f"`{flag.group(1)}` is not an option of any script")
            if flag.group(1) == "--set" and flag.group(2):
                key = flag.group(2).split("=")[0]
                if not config_has(cfg, key):
                    rep.error(where, f"--set {key}: no such key in configs/default.toml")
            continue
        key = re.fullmatch(r"([a-z_]+)\.([a-z_.]+)", span)
        if key and isinstance(cfg.get(key.group(1)), dict) and not config_has(cfg, span):
            rep.error(where, f"`{span}`: no such key in configs/default.toml")


def check_inline_paths(name: str, prose: str, rep: Report) -> None:
    for m in re.finditer(r"`([^`\n]+)`", prose):
        token = m.group(1).strip()
        if REPO_PATH.match(token) and "<" not in token and "*" not in token:
            if not (ROOT / token.rstrip("/")).exists():
                say = rep.error if "/" in token else rep.warn
                say(f"{name}:{line_of(prose, m.start())}", f"`{token}` does not exist in the repo")


def sections(md: str, prose: str) -> list[tuple[str, str, int]]:
    """(title, body, first line) per heading of level 1-3. Headings are read from the prose
    (code blanked) and bodies from the full markdown, so code blocks count toward their section."""
    parts, title, buf, start = [], "(top)", [], 1
    for i, (line, plain) in enumerate(zip(md.splitlines(), prose.splitlines()), 1):
        if re.match(r"^#{1,3}\s", plain):
            parts.append((title, "\n".join(buf), start))
            title, buf, start = plain.lstrip("# ").strip(), [], i
        else:
            buf.append(line)
    parts.append((title, "\n".join(buf), start))
    return parts


def check_numbers(name: str, md: str, prose: str, label: str, rep: Report) -> None:
    known = docs_numbers()
    for m in SCORE.finditer(md):
        if not traceable(m.group(0), known):
            rep.error(f"{name}:{line_of(md, m.start())}", f"{m.group(0)} appears in no file under docs/; cite where it comes from")
    if not label:
        return
    full_sections = sections(md, prose)
    for title, body, start in full_sections:
        if SCORE.search(body) and label.lower() not in (title + body).lower():
            rep.error(f"{name}:{start}", f'section "{title}" shows scores but never says "{label}"')


def check_headings(name: str, prose: str, required: list[str], rep: Report) -> None:
    present = {slugify(h) for h in re.findall(r"^#{1,6}\s+(.+?)\s*$", prose, re.M)}
    present |= {slugify(s) for s in re.findall(r"<summary>(.*?)</summary>", prose, re.S)}
    for h in required:
        if not any(slug.startswith(slugify(h)) for slug in present):
            rep.error(name, f'required heading "{h}" is missing (repo-profile readme.required_headings)')


# ---------------------------------------------------------------- assets

SVG_NS = "{http://www.w3.org/2000/svg}"


def check_svg(path: Path, label: str, rep: Report) -> None:
    rel = str(path.relative_to(ROOT))
    raw = path.read_text()
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        rep.error(rel, f"not valid XML: {exc}")
        return
    if "viewBox" not in root.attrib:
        rep.error(rel, "no viewBox, so it will not scale")
    if root.find(f"{SVG_NS}title") is None:
        rep.error(rel, "no <title> as first-level child (screen readers and hover text)")
    for bad in ("script", "foreignObject"):
        if next(root.iter(f"{SVG_NS}{bad}"), None) is not None:
            rep.error(rel, f"<{bad}> does not render when GitHub shows an SVG as an image")
    if re.search(r"""(?:href|src)\s*=\s*["']https?:""", raw) or re.search(r"url\(\s*['\"]?https?:", raw) or "@import" in raw:
        rep.error(rel, "loads a remote resource; GitHub renders SVGs as images, so it will not load")
    drawn = [el.get("aria-label", "") for el in root.iter() if el.get("aria-label")]
    if not drawn and next(root.iter(f"{SVG_NS}use"), None) is not None:
        rep.error(rel, "outlined text carries no aria-label, so what the figure draws cannot be checked; "
                       "rebuild it with docs/assets/build_figures.py")
    text = " ".join([t.strip() for t in root.itertext() if t.strip()] + drawn)
    if label and SCORE.search(text) and label.lower() not in text.lower():
        rep.error(rel, f'figure shows scores but never says "{label}"')
    known = docs_numbers()
    for m in SCORE.finditer(text):
        if not traceable(m.group(0), known):
            rep.error(rel, f"{m.group(0)} appears in no file under docs/")


def png_size(path: Path) -> tuple[int, int] | None:
    head = path.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def check_profile(profile: dict, rep: Report) -> None:
    about = profile.get("about", {})
    desc = about.get("description", "")
    if not desc:
        rep.error("repo-profile", "about.description is empty")
    elif len(desc) > 350:
        rep.error("repo-profile", f"about.description is {len(desc)} characters; GitHub allows 350")
    banned = profile.get("readme", {}).get("banned_phrases", DEFAULT_BANNED)
    for phrase in banned:
        if re.search(rf"(?<![\w-]){re.escape(phrase)}(?![\w-])", desc, re.I):
            rep.error("repo-profile", f'about.description uses stock phrase "{phrase}"')
    topics = about.get("topics", [])
    if len(topics) > 20:
        rep.error("repo-profile", f"{len(topics)} topics; GitHub allows 20")
    for t in topics:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,49}", t):
            rep.error("repo-profile", f'topic "{t}" must be lowercase letters, digits and hyphens, at most 50')
    preview = about.get("social_preview")
    if preview:
        p = ROOT / preview
        size = png_size(p) if p.exists() else None
        if not p.exists():
            rep.error("repo-profile", f"social_preview {preview} does not exist")
        elif size is None:
            rep.error("repo-profile", f"social_preview {preview} is not a PNG")
        elif size[0] < 640 or abs(size[0] - 2 * size[1]) > 2:
            rep.error("repo-profile", f"social_preview is {size[0]}x{size[1]}; GitHub wants 2:1, ideally 1280x640")


# ---------------------------------------------------------------- driver

def run_checks() -> Report:
    rep = Report()
    profile = load_profile()
    rcfg = profile.get("readme", {})
    readme = ROOT / rcfg.get("path", "README.md")
    label = rcfg.get("results_label", "synthetic")
    md = readme.read_text()
    prose, blocks = split_code(md)
    name = readme.name

    images = check_links(name, md, prose, readme.parent, rep)
    check_sanitizer(name, prose, rep)
    check_voice(name, prose, rcfg.get("banned_phrases", DEFAULT_BANNED), rcfg.get("max_badges", 3), rep)
    for m in re.finditer(r"\b\d+\s+(?:unit\s+|passing\s+)?tests\b|\b\d+\s+passed\b", md, re.I):
        rep.error(f"{name}:{line_of(md, m.start())}", f'hard-coded "{m.group(0)}" goes stale; drop the count')
    check_commands(name, blocks, rep)
    check_inline_code(name, prose, rep)
    check_inline_paths(name, prose, rep)
    check_numbers(name, md, prose, label, rep)
    check_headings(name, prose, rcfg.get("required_headings", []), rep)
    if not profile:
        rep.warn("repo-profile", f"{PROFILE.relative_to(ROOT)} not found; About box is unchecked")
    else:
        check_profile(profile, rep)

    assets = ROOT / "docs" / "assets"
    preview = profile.get("about", {}).get("social_preview", "")
    preview_source = str(Path(preview).with_suffix(".svg")) if preview else None
    if assets.exists():
        for svg in sorted(assets.glob("*.svg")):
            check_svg(svg, label, rep)
            rel = str(svg.relative_to(ROOT))
            if rel not in images and rel != preview_source:
                rep.warn(rel, "not referenced from the README")
    return rep


def gh_command(profile: dict) -> str:
    about = profile.get("about", {})
    parts = ["gh repo edit", f"--description {shlex.quote(about.get('description', ''))}"]
    if about.get("homepage"):
        parts.append(f"--homepage {shlex.quote(about['homepage'])}")
    parts += [f"--add-topic {t}" for t in about.get("topics", [])]
    return " \\\n  ".join(parts)


RELEVANT = re.compile(r"^(?:README\.md|\.github/repo-profile\.toml|docs/.+|configs/.+\.toml|[\w-]+\.py"
                      r"|genemila/cli_common\.py|tools/readme_check\.py)$")
RELEVANT_CMD = re.compile(r"\bgit\s+(?:commit|merge|pull|cherry-pick|rebase|checkout|switch)\b"
                          r"|README\.md|repo-profile|docs/|configs/|build_figures")


def hook_relevant(tool_input: dict) -> bool:
    if "command" in tool_input:
        return bool(RELEVANT_CMD.search(tool_input.get("command") or ""))
    target = Path(tool_input.get("file_path") or "")
    try:
        rel = target.resolve().relative_to(ROOT).as_posix() if target.is_absolute() else target.as_posix()
    except ValueError:
        return False
    return bool(RELEVANT.match(rel))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hook", action="store_true", help="Claude Code PostToolUse hook mode")
    ap.add_argument("--gh-command", action="store_true", help="print the gh command that applies the About box")
    args = ap.parse_args(argv)

    if tomllib is None:
        if args.hook:  # an old interpreter must not turn every edit into a hook error
            return 0
        print("tools/readme_check.py needs Python 3.11 or newer (tomllib)", file=sys.stderr)
        return 1
    if args.gh_command:
        print(gh_command(load_profile()))
        return 0
    if args.hook:
        try:
            event = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            return 0
        if not hook_relevant(event.get("tool_input") or {}):
            return 0
        rep = run_checks()
        if rep.errors:
            print("README check failed (tools/readme_check.py):", file=sys.stderr)
            for e in rep.errors:
                print(f"  - {e}", file=sys.stderr)
            print("Fix these before committing; the readme-designer agent can review the page as a whole.", file=sys.stderr)
            return 2
        return 0

    rep = run_checks()
    for w in rep.warnings:
        print(f"warning  {w}")
    for e in rep.errors:
        print(f"error    {e}")
    print(f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
