# CLAUDE.md

Guidance for Claude Code working in this repository (CSC299 project).

## Project

SkillSwap is a local Flask web app for trading services. `problem.md` holds the
original requirements (R1–R5). `spec.md` is the source of truth for behavior.
Read both before making changes.

## Rules

- Implement only what `spec.md` requires. Do not add features, and check the
  "Out of scope" section before adding anything.
- If a requirement is unclear, ask instead of guessing. Update `spec.md` when a
  decision changes.
- Keep the project small: Flask, Jinja templates, and a JSON file. Add no other
  runtime dependencies without asking.
- Write or update tests before or with each code change. Every requirement
  R1–R5 must have tests.
- Do not commit or push unless asked.

## Planned layout

- `skillswap/core.py`: pure logic with no Flask imports. Covers the JSON store,
  profile creation, adding services, normalization, and `find_matches`.
- `skillswap/app.py`: `create_app(data_path=...)` factory and routes. Keep the
  routes thin and call into `core.py`.
- `skillswap/__main__.py`: entry point for `python -m skillswap`.
- `skillswap/templates/`: `index.html` and `profile.html`.
- `tests/`: pytest tests. Use `tmp_path` for the data file and never touch the
  real `data.json`.
- `data.json`: runtime data, gitignored.

## Commands

- Run the app: `uv run python -m skillswap`, then open http://127.0.0.1:5000
- Run the tests: `uv run pytest`

## Conventions

- Compare services with `normalize()`: trim the ends, collapse whitespace, and
  lowercase. Store the original trimmed text.
- Profile names are unique after normalization.
- Save to the JSON file after every change.
