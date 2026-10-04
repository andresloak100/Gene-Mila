"""tools/readme_check.py: each rule fires on a bad page and stays quiet on a good one."""

from __future__ import annotations

import importlib.util
import json
import struct
import sys
import zlib
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "readme_check", Path(__file__).resolve().parent.parent / "tools" / "readme_check.py")
rc = importlib.util.module_from_spec(SPEC)
sys.modules["readme_check"] = rc
SPEC.loader.exec_module(rc)

GOOD = """# Gene-Mila

<p align="center"><img src="docs/assets/plate.svg" alt="the loop" width="800"></p>

Linear models only. See [the notes](docs/NOTES.md) and [running it](#quick-start).

## Results on synthetic data

The best feature reached 0.7775 (baseline 0.605).

## Quick start

```bash
python run.py --minutes 2 --set run.workers=4   # dry run
python -m pytest -q
```

Configuration lives in `configs/default.toml`.
"""

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><title>plate</title>
<text>synthetic: 0.7775</text></svg>"""


def png(w: int, h: int) -> bytes:
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
    raw = b"".join(b"\x00" + b"\x00" * (w * 3) for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "default.toml").write_text("[run]\nworkers = 4\n")
    (tmp_path / "genemila").mkdir()
    (tmp_path / "genemila" / "cli_common.py").write_text('ap.add_argument("--run")\n')
    (tmp_path / "run.py").write_text('ap.add_argument("--minutes")\nap.add_argument("--set")\n')
    (tmp_path / "docs" / "assets").mkdir(parents=True)
    (tmp_path / "docs" / "NOTES.md").write_text("best 0.7775, baseline 0.6054\n")
    (tmp_path / "docs" / "assets" / "plate.svg").write_text(SVG)
    (tmp_path / "docs" / "assets" / "preview.png").write_bytes(png(640, 320))
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "repo-profile.toml").write_text(
        '[about]\ndescription = "Agents write features; ridge decides."\n'
        'topics = ["perturb-seq", "ai-agents"]\nsocial_preview = "docs/assets/preview.png"\n'
        '[readme]\nrequired_headings = ["Quick start"]\n')
    (tmp_path / "README.md").write_text(GOOD)
    monkeypatch.setattr(rc, "ROOT", tmp_path)
    monkeypatch.setattr(rc, "PROFILE", tmp_path / ".github" / "repo-profile.toml")
    return tmp_path


def errors(repo: Path, readme: str | None = None) -> list[str]:
    if readme is not None:
        (repo / "README.md").write_text(readme)
    return rc.run_checks().errors


def test_good_page_passes(repo):
    rep = rc.run_checks()
    assert rep.errors == []


@pytest.mark.parametrize("snippet, expected", [
    ("[x](docs/missing.md)", "does not exist"),
    ("[x](#nowhere)", "matches no heading"),
    ('<img src="docs/assets/plate.svg">', "no alt text"),
    ("![](docs/assets/plate.svg)", "no alt text"),
    ('<div style="color:red">x</div>', "style attributes"),
    ("A powerful, seamless lab.", "stock phrase"),
    ("- \U0001F680 fast", "starts with an emoji"),
    ("All 72 tests pass.", "goes stale"),
    ("See `genemila/nothere.py`.", "does not exist in the repo"),
    ("\n## Results\n\nScore 0.7775.\n", 'never says "synthetic"'),
    ("We reached 0.8123 on synthetic data.", "appears in no file under docs/"),
    ("```bash\npython run.py --bogus 1\n```", "has no --bogus option"),
    ("```bash\npython run.py --set nope.key=1\n```", "no such key"),
    ("```bash\npython nosuch.py\n```", "does not exist"),
    ("```bash\npython run.py --set=nope.key=1\n```", "no such key"),
    ("Run `python run.py --bogus` first.", "has no --bogus option"),
    ("Pass `--bogus` to skip it.", "not an option of any script"),
    ("Set `run.nope` in the config.", "no such key"),
    ("Pass `--set run.nope=2`.", "no such key"),
    ("We ran 3 passed.", "goes stale"),
])
def test_each_rule_fires(repo, snippet, expected):
    found = errors(repo, GOOD + "\n" + snippet + "\n")
    assert any(expected in e for e in found), found


def test_quiet_on_legitimate_text(repo):
    page = GOOD + (
        "\nFiles: `summary.md`, `lab.db`, `run.workers`, `--minutes`, `--run runs/<id>`.\n"
        "Override with `--set section.key=value`. Next-generation sequencing, 1 test at a time.\n"
        "Their loader is `pertdata.py`.\n")
    rep_errors = errors(repo, page)
    assert rep_errors == [], rep_errors
    assert any("pertdata.py" in w for w in rc.run_checks().warnings)


def test_single_quoted_flags_count(repo):
    (repo / "run.py").write_text("ap.add_argument('--minutes')\nap.add_argument('--set')\n")
    assert errors(repo) == []


def test_code_comments_are_not_headings(repo):
    # the `# ...` line must not start a section, and a score in the code still needs the label
    page = GOOD + "\n## Commands\n\n```bash\n# notes\npython run.py --minutes 2   # reaches 0.7775\n```\n"
    found = errors(repo, page)
    assert any('"Commands" shows scores' in e for e in found), found
    assert not any('"notes"' in e for e in found), found


def test_slug_keeps_code_text():
    assert rc.slugify("Outputs of a run (`runs/<id>/`)") == "outputs-of-a-run-runsid"


def test_svg_drawn_numbers_are_traced(repo):
    (repo / "docs" / "assets" / "plate.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><title>plate, synthetic</title>'
        '<g aria-label="best 0.9123"/></svg>')
    found = errors(repo)
    assert any("0.9123 appears in no file" in e for e in found), found


def test_svg_outlines_without_labels_are_flagged(repo):
    (repo / "docs" / "assets" / "plate.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><title>plate, synthetic</title>'
        '<defs><path id="a" d="M0 0"/></defs><g><use href="#a"/></g></svg>')
    assert any("carries no aria-label" in e for e in errors(repo))


def test_rounded_numbers_trace_to_docs(repo):
    assert errors(repo, GOOD.replace("0.7775", "0.778")) == []


def test_required_heading(repo):
    found = errors(repo, GOOD.replace("## Quick start", "## Getting going").replace("#quick-start", "#getting-going"))
    assert any('required heading "Quick start"' in e for e in found), found


def test_svg_rules(repo):
    (repo / "docs" / "assets" / "plate.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="https://x/y.png"/><text>0.7775</text></svg>')
    found = errors(repo)
    for expected in ("no viewBox", "no <title>", "remote resource", 'never says "synthetic"'):
        assert any(expected in e for e in found), (expected, found)


def test_profile_limits(repo):
    (repo / ".github" / "repo-profile.toml").write_text(
        '[about]\ndescription = "' + "x" * 351 + '"\ntopics = ["Bad Topic"]\n'
        'social_preview = "docs/assets/plate.svg"\n')
    found = errors(repo)
    for expected in ("350", "lowercase", "not a PNG"):
        assert any(expected in e for e in found), (expected, found)


def test_hook_mode_ignores_unrelated_files(repo, monkeypatch, capsys):
    (repo / "README.md").write_text(GOOD + "\nA powerful lab.\n")
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps({"tool_input": {"file_path": "genemila/lab.py"}})))
    assert rc.main(["--hook"]) == 0
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps({"tool_input": {"file_path": str(repo / "README.md")}})))
    assert rc.main(["--hook"]) == 2
    assert "stock phrase" in capsys.readouterr().err


@pytest.mark.parametrize("tool_input, runs", [
    ({"command": "git commit -m 'x'"}, True),
    ({"command": "sed -i 's/a/b/' docs/x.md"}, True),
    ({"command": "ls -la"}, False),
    ({"file_path": "configs/default.toml"}, True),
    ({"file_path": "run.py"}, True),
    ({"file_path": "genemila/lab.py"}, False),
])
def test_hook_watches_commands_configs_and_scripts(repo, monkeypatch, tool_input, runs):
    (repo / "README.md").write_text(GOOD + "\nA powerful lab.\n")
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps({"tool_input": tool_input})))
    assert rc.main(["--hook"]) == (2 if runs else 0)


def test_hook_is_silent_without_tomllib(repo, monkeypatch):
    (repo / "README.md").write_text(GOOD + "\nA powerful lab.\n")
    monkeypatch.setattr(rc, "tomllib", None)
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps({"tool_input": {"file_path": "README.md"}})))
    assert rc.main(["--hook"]) == 0
    assert rc.main([]) == 1


def test_gh_command(repo, capsys):
    assert rc.main(["--gh-command"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("gh repo edit") and "--add-topic perturb-seq" in out
