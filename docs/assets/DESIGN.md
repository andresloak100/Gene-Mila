# Figure design

The README figures are drawn by `build_figures.py` in this folder and are not edited by hand.
To change a figure, change the script or the run report it reads, then run:

```bash
pip install fonttools==4.66.1
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
   README gives the same information in its `alt` text or the surrounding prose. Every outlined
   line of text keeps its words in an `aria-label`, which is also what `tools/readme_check.py`
   reads when it traces numbers and the synthetic label.
7. **Layout is checked when drawing.** A missing glyph, a legend that runs into the footer, or
   text that overflows a panel stops the script with an error instead of producing a broken
   figure. Look at every changed figure rendered in light and dark before committing it.

## Palette

| Token | Light | Dark | Meaning |
|---|---|---|---|
| `paper` | `#F7F5EF` | `#12171D` | plate background |
| `panel` | `#EFECE3` | `#1A2028` | inset panels |
| `ink` | `#1B2027` | `#E8EBEE` | text, Python-owned steps |
| `soft` | `#555E69` | `#A9B1BA` | secondary text |
| `faint` | `#646C75` | `#7F8892` | axis labels, secondary values |
| `rule` / `grid` | `#D9D4C7` / `#E6E1D5` | `#2D343D` / `#202730` | hairlines |
| `pi` | `#3C4FA8` | `#93A3FF` | the planner (Claude) |
| `worker` | `#B07415` | `#E5B04E` | worker LLMs and the code they write |
| `gain` | `#08766A` | `#3CC4B1` | scores, the best model, things that improved |
| `clock` | `#C03C20` | `#FF7A5C` | the deadline, guards, failures |
| `base` | `#5F666E` | `#858D97` | baselines |

Colour always means the same actor or outcome across figures; do not reuse a token for a
different meaning. Text colours (`ink`, `soft`, `faint`, and the accents used for words) keep at
least 4.5:1 contrast on `paper` and `panel` in both themes, so small mono text stays readable.
Kickers on the loop's stations are set in `ink`; the coloured bar beside them carries the role.

## Type

| Face | Used for |
|---|---|
| Fraunces 600 (and 400 italic) | headlines, the wordmark, large numbers |
| IBM Plex Sans 400 / 500 | labels and explanatory text |
| IBM Plex Mono 400 / 500 | kickers (upper case, tracked), axis values, identifiers, code |

Both families are under the SIL Open Font License (`fonts/OFL-*.txt`). Sizes on a 960-wide
plate: headline 25, body 12 to 14, kicker 11.5, footnote 11. Nothing smaller than 11.
