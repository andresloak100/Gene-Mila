# Notes for Claude sessions in this repository

## README and repository presentation

The README, the figures in `docs/assets/` and the GitHub About profile in
`.github/repo-profile.toml` are the project's public face. When a change touches any of them,
or changes what they describe (command-line flags, `configs/default.toml`, datasets, metrics,
results under `docs/`):

1. Run `python tools/readme_check.py` and fix every error. A PostToolUse hook in
   `.claude/settings.json` runs it automatically after edits to those files, and CI runs it on
   pull requests.
2. Ask the `readme-designer` agent (`.claude/agents/readme-designer.md`) to review the page
   before committing. It owns the judgement calls the checker cannot make: whether the page is
   specific to this project, accurate and well designed.
