# Notes for Claude sessions in this repository

## Read AGENTS.md first

`AGENTS.md` holds the rules every agent here follows, Claude sessions and outside agents such as
Astra alike, and `HANDOFF.md` section 1 holds the shared state that whoever is working keeps
current. Read both at the start of every session; they win over anything below that conflicts.

@AGENTS.md

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
