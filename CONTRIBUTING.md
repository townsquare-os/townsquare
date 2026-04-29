# Contributing to townsquare

## Dev setup

```bash
git clone https://github.com/townsquare-os/townsquare
cd townsquare
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,google,all]"
townsquare gen-secrets   # paste output into .env
townsquare init-db
townsquare serve --reload
```

## What to contribute

In v0.1 the highest-leverage contributions are:

- New connectors (Slack, Notion, GitHub, Linear, Asana, Confluence)
- Better selector heuristics (graph-aware fanout)
- Frontend polish (HTMX patterns, Tailwind components)
- Migration recipes (Alembic)
- Helm chart for k8s deploy

## Style

- `ruff check src/` and `ruff format src/` before PR.
- `pytest -v` green.
- Imperative commit subjects (~50 chars). Body explains *why*.
- No bot-generated commit trailers.

## License

Apache 2.0. By contributing you agree your work is licensed under the same.
