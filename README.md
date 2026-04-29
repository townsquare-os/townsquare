<p align="center">
  <img src="https://raw.githubusercontent.com/townsquare-os/townsquare/main/docs/assets/banner.svg" alt="townsquare — the self-hostable company OS" width="100%">
</p>

<p align="center">
  <a href="https://github.com/townsquare-os/townsquare/actions/workflows/ci.yml?query=branch%3Amain"><img src="https://github.com/townsquare-os/townsquare/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="Apache 2.0"></a>
  <a href="https://github.com/townsquare-os/townsquare/blob/main/pyproject.toml"><img src="https://img.shields.io/badge/python-3.10–3.13-blue?logo=python&logoColor=white" alt="Python 3.10–3.13"></a>
  <a href="https://github.com/townsquare-os/townsquare/releases"><img src="https://img.shields.io/badge/status-alpha-orange" alt="alpha"></a>
</p>

<p align="center"><strong>Your company's brain — but you own it.</strong></p>

<p align="center">
  Sign in with Google. Connect your Gmail, Drive, Slack, and GitHub.<br>
  Ask any question — townsquare answers it across your whole company,<br>
  with each person's data queried under their own credentials.
</p>

<p align="center">
  <a href="docs/SELF_HOSTING.md"><strong>Self-host in 30 minutes →</strong></a>
</p>

---

## How it feels

```
You:  "What's the status of the Q3 launch?"

townsquare:
  → fans out to Bob, Carol, and Dan (they're in #q3-launch + the recurring meeting)
  → each query runs under that person's own Google + Slack creds
  → 4.2 seconds later

  Beta freeze is set for May 14 [via bob@acme.com · calendar].
  Carol's design doc passed legal review on Apr 28 [via carol@acme.com · drive].
  Dan flagged an open auth bug yesterday in #q3-launch [via dan@acme.com · slack].
```

Carol's draft job-offer email never reaches the central agent. Slack DMs Bob isn't in stay invisible. **Privacy is enforced at the source, not bolted on after.**

## Why it's different

- **Your infrastructure, your data.** Self-host with one `make up`. The only outbound calls are to your chosen LLM and the data sources each user connected — nothing else. No telemetry. No phone-home.
- **Per-user, not per-bot.** Most "company brain" tools install one Slack bot that sees everything the bot is invited to. townsquare uses each employee's *own* OAuth. Removable, auditable, scoped.
- **Apache 2.0, no strings.** Fork it, run it, sell it. No commercial restrictions.

## Get it running

```bash
git clone https://github.com/townsquare-os/townsquare
cd townsquare
cp example.env .env
make gen-secrets         # paste FERNET_KEY + SECRET_KEY into .env
# fill GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, WORKSPACE_DOMAIN, ANTHROPIC_API_KEY
make up
open http://localhost:8000
```

That's the whole installation. The full step-by-step (Google OAuth setup, TLS, first admin) is in [docs/SELF_HOSTING.md](docs/SELF_HOSTING.md).

## Connectors today

| Source | How it connects | Privacy unit |
|---|---|---|
| Gmail | granted at SSO | per-user |
| Google Drive | granted at SSO | per-user |
| Google Calendar | granted at SSO | per-user |
| Slack | per-user OAuth (xoxp, not bot) | per-user |
| GitHub | per-user fine-grained PAT | per-user |
| Notion · Linear · Jira | coming in v0.2 | per-user |

## Documentation

| | |
|---|---|
| [Self-host in 30 min](docs/SELF_HOSTING.md) | The end-to-end setup guide |
| [Google OAuth setup](docs/GOOGLE_OAUTH_SETUP.md) | The fiddly bit, broken down |
| [Operations](docs/OPERATIONS.md) | Backups, upgrades, secret rotation |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common failure modes |
| [SPEC.md](SPEC.md) | RFC-2119 spec — implement townsquare in any language |
| [Roadmap](ROADMAP.md) | What's coming next |
| [Contributing](CONTRIBUTING.md) | The contract every connector must satisfy |
| [Security](SECURITY.md) | Reporting vulnerabilities, supported versions |

## Built with

Python · FastAPI · Postgres · HTMX · Tailwind · Anthropic Claude · Authlib · cryptography.fernet

## License

[Apache 2.0](LICENSE) — free for any use, including commercial.

---

<p align="center">
  <sub>Built by <a href="https://github.com/SwathiMystery">Swathi</a>, released as OSS so any company can run their own.<br>
  If townsquare helps you — ⭐ the repo. It's the only signal we get.</sub>
</p>
