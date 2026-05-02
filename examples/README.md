# Examples

Runnable scripts that show one feature each. Some import `townsquare.*` directly (library usage); others call a running server’s HTTP endpoints (integration patterns). Think of them as reference implementations for specific workflows.

## Available scripts

| Script                                   | What it does |
| ---------------------------------------- | ------------ |
| _(none yet — be the first contributor!)_ |              |

## How to run

First: get townsquare running. The full setup is in [docs/SELF_HOSTING.md](../docs/SELF_HOSTING.md). Quick version:

```bash
git clone https://github.com/townsquare-os/townsquare
cd townsquare
cp example.env .env
make gen-secrets         # paste into .env
# fill GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, WORKSPACE_DOMAIN, ANTHROPIC_API_KEY
make up
```

Install Python dependencies locally (examples need them):

```bash
python -m venv .venv
source .venv/bin/activate

# Minimal (works for most examples)
pip install -e ".[dev]"

# If the example uses external connectors (Slack, Notion, GitHub, etc.)
pip install -e ".[all,dev]"

# Or, for very simple examples with no extras
pip install -e .
```

Run any example:

```bash
source .venv/bin/activate
python examples/<script>.py
```

Each script reads `.env` from the repo root. Some need extra connectors (`SLACK_CLIENT_ID`, GitHub PAT) — check the script's header comment for specifics.

## What makes a good example

- Demonstrates **one** workflow (federated query, connector usage, agent invocation, wiki/CRM operations, user management).
- Uses either `townsquare.*` imports (library usage) or HTTP calls to a running server (integration patterns).
- Loads `.env` from the repo root (e.g., via `python-dotenv` or `townsquare.settings.get_settings()`).
- Inline comments explaining key decisions and API patterns.
- Graceful error handling with helpful messages.
- Header comment listing required `.env` variables beyond the defaults.

When you add a script, update the table above.
