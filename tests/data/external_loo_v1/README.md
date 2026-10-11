# external_loo report written before the second look

`report.json` and `report.md` were written on 2026-10-11 by `tools/external_loo.py` as it stood before
`external_krr` and `external_stack_krr` were added (five predictors, no `added_after_first_reading` key), on a small
synthetic bundle: `genemila.data.synthetic.generate(n_genes=40, n_modules=4, n_tfs=8, n_perts=14, n_control=120,
cells_per_pert=12, seed=5)`, its public part, and an external file from `_write_external` in
`tests/test_external_loo.py` (mode "signal", the first training target dropped, the second written as a zero-cell
row), run with `--k 3` and the default alpha grid.

`test_report_written_before_the_second_look_renders_byte_identical` asserts that the current code renders this JSON
to exactly this markdown, so re-rendering an old twin with `--from-json` never changes it. Do not regenerate these
files with newer code: they are the frozen output of the old code.
