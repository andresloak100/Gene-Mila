# Figure design

The README figures are drawn by `build_figures.py` in this folder and are not edited by hand.
To change a figure, change the script or the run report it reads, then run:

```bash
pip install fonttools
python docs/assets/build_figures.py
python tools/readme_check.py
```

## Rules

1. **One idea per figure, stated in its headline.** The headline is a claim ("Agents propose
   features. The numbers decide which stay."), not a label ("Results").
2. **Data comes from `docs/`.** The script parses run reports (`docs/example_run/summary.md`,
   `analysis.md`); it never types a score in. Each SVG says where its numbers came from in a
   comment at the top and in its footer.
3. **Synthetic stays labelled.** Until a real dataset has been scored, every figure that shows a
   score says "synthetic" in its kicker or footer. `tools/readme_check.py` enforces this.
4. **Self-contained SVG.** GitHub shows README images inside an `<img>`, which blocks fonts,
   scripts and remote files. Lettering is therefore converted to outlines from the fonts in
   `fonts/`, colours live in an internal stylesheet, and nothing is loaded from elsewhere.
5. **Light and dark from one file.** Colours are CSS classes (`f-ink` for fill, `s-ink` for
   stroke); the stylesheet swaps the palette under `prefers-color-scheme: dark`. Every figure
   sits on its own paper-coloured plate, so it stays legible if the two themes disagree.
6. **Accessible.** Each SVG has a `<title>` and a `<desc>` that states the numbers, and the
   README gives the same information in its `alt` text or the surrounding prose.

## Palette

| Token | Light | Dark | Meaning |
|---|---|---|---|
| `paper` | `#F7F5EF` | `#12171D` | plate background |
| `panel` | `#EFECE3` | `#1A2028` | inset panels |
| `ink` | `#1B2027` | `#E8EBEE` | text, Python-owned steps |
| `soft` | `#555E69` | `#A9B1BA` | secondary text |
| `faint` | `#8A929B` | `#77808A` | axis labels, footers |
| `rule` / `grid` | `#D9D4C7` / `#E6E1D5` | `#2D343D` / `#202730` | hairlines |
| `pi` | `#3C4FA8` | `#93A3FF` | the planner (Claude) |
| `worker` | `#B07415` | `#E5B04E` | worker LLMs and the code they write |
| `gain` | `#0B7A6E` | `#3CC4B1` | scores, the best model, things that improved |
| `clock` | `#D4452A` | `#FF7A5C` | the deadline, guards, rejections |
| `base` | `#9AA1A9` | `#6E7781` | baselines |

Colour always means the same actor or outcome across figures; do not reuse a token for a
different meaning.

## Type

| Face | Used for |
|---|---|
| Fraunces 600 (and 400 italic) | headlines, the wordmark, large numbers |
| IBM Plex Sans 400 / 500 | labels and explanatory text |
| IBM Plex Mono 400 / 500 | kickers (upper case, tracked), axis values, identifiers, code |

Both families are under the SIL Open Font License (`fonts/OFL-*.txt`). Sizes on a 960-wide
plate: headline 25, body 12 to 14, kicker 11.5, footnote 11. Nothing smaller than 11.
