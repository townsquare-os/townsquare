<div align="center">

# townsquare

### *The self-hostable company OS.*

Google Workspace SSO. Each employee connects their own data. Privacy-preserving federation across users. One question, your whole company's collective answer — without giving up control of the data.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?logo=python&logoColor=white)](https://pypi.org/project/townsquare/)
[![Status](https://img.shields.io/badge/status-alpha-orange)](https://github.com/townsquare-os/townsquare/releases)

</div>

---

## Why townsquare exists

Every company has the same problem: institutional knowledge is scattered across Gmail, Drive, Slack, Notion, GitHub, Calendar, and a dozen SaaS tools. Nobody can find anything. AI assistants help — but only if they have the context.

The current options for a "company brain" all require giving up something:

| Option | What you give up |
|---|---|
| **Glean** ($7.2B) | Closed-source, expensive, your data leaves your infrastructure |
| **Scout (Agno)** | UI hosted by a third party, no SSO, single bot token sees everyone's data |
| **Mem0 enterprise** | Closed-source, central aggregation, no per-user privacy |
| **DIY** | 6 months of plumbing |

**townsquare is the fourth option.** Apache 2.0, fully self-hosted, Google Workspace SSO, per-user data connections, privacy enforced at the source.

## The novel idea: federated MCP per user

Instead of central service accounts that ingest everyone's data and bolt RBAC on top, townsquare flips it. Each employee connects *their* data sources with *their* OAuth credentials. When someone asks a question, townsquare federates the query across just the employees whose data is relevant — and each query runs under that employee's permissions, at the source.

```
Alice asks: "What's the status of the Q3 launch?"

townsquare:
  ↓
  Routing: Bob, Carol, and Dan are in #q3-launch and on the recurring calendar
  ↓
  Fanout in parallel:
    Bob's Gmail   → searches under Bob's creds (his filters, his perms)
    Carol's Drive → searches under Carol's creds
    Dan's Calendar → searches under Dan's creds
  ↓
  Aggregate, cite per-source-per-user, return to Alice with attribution

Privacy: Carol's draft email about her job offer never reaches the central agent.
Her sidecar refuses to expose drafts. Same for Slack DMs, private Drive folders.
```

## Self-host in 30 minutes

Full step-by-step at [docs/SELF_HOSTING.md](docs/SELF_HOSTING.md). Quick version:

```bash
# 1. Clone
git clone https://github.com/townsquare-os/townsquare
cd townsquare

# 2. Configure
cp example.env .env
make gen-secrets       # → paste FERNET_KEY + SECRET_KEY into .env
# Edit .env: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, WORKSPACE_DOMAIN, ANTHROPIC_API_KEY

# 3. Boot
make up
make logs              # watch the api come up

# 4. Visit
open http://localhost:8000
# Sign in with your @yourcompany.com Google account
# Promote yourself to admin:
docker compose exec api townsquare admin promote you@yourcompany.com
```

That's it. Your colleagues can now sign in with their company Google accounts.

### What you need before starting

- A **Google Workspace** for your company (the OAuth client must be configured as User Type = Internal — see [docs/GOOGLE_OAUTH_SETUP.md](docs/GOOGLE_OAUTH_SETUP.md))
- A **Linux host** with Docker + Docker Compose (1 GB RAM minimum, 2 GB recommended)
- An **Anthropic API key** ([console.anthropic.com](https://console.anthropic.com))
- A **DNS name** + TLS for production (Caddy auto-provisions Let's Encrypt; see SELF_HOSTING.md)

### What v0.1 ships

| Feature | Status |
|---|---|
| Google Workspace SSO with domain restriction | ✓ |
| Gmail / Drive / Calendar connectors | ✓ |
| Per-user encrypted OAuth token storage | ✓ |
| Federation router (parallel + budget + isolated failures + attribution) | ✓ |
| Central agent (Anthropic Claude with tool use) | ✓ |
| HTMX + Tailwind web UI | ✓ |
| Wiki with versioning + agent read/write tools | ✓ |
| Admin CLI (promote, deactivate, forget) | ✓ |
| Docker Compose self-host | ✓ |
| 23 unit tests, ruff clean | ✓ |

See [ROADMAP.md](ROADMAP.md) for v0.2+ (Slack, Notion, GitHub, OpenTelemetry, Helm).

## Documentation

| Doc | What it covers |
|---|---|
| [SELF_HOSTING.md](docs/SELF_HOSTING.md) | End-to-end self-host walkthrough (30 min) |
| [GOOGLE_OAUTH_SETUP.md](docs/GOOGLE_OAUTH_SETUP.md) | Google Cloud Console step-by-step (10 min) |
| [OPERATIONS.md](docs/OPERATIONS.md) | Backups, upgrades, secret rotation, monitoring, security checklist |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common failure modes |
| [SPEC.md](SPEC.md) | RFC 2119 normative spec — implement townsquare in any language |
| [ROADMAP.md](ROADMAP.md) | v0.2 / v0.3 / v0.4 plans |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Adding connectors, backends, frontend |

## Operations cheatsheet

```bash
make up                  # start db + api
make down                # stop
make restart             # restart api after env changes
make logs                # tail api logs
make rebuild             # full rebuild after pulling new code
make backup              # gzipped pg_dump → ./backups/<UTC stamp>.sql.gz
make admin-list-users    # see registered users
```

Full admin CLI surface in [OPERATIONS.md](docs/OPERATIONS.md).

## Trust posture

- All data stays on your infrastructure. The only outbound calls are: (a) Anthropic API (your key), and (b) per-user data sources (Google APIs under each user's own token).
- No telemetry. No phone-home. No analytics.
- Per-user isolation: Bob can never see Carol's data unless Google's source-side permissions allow it.
- All OAuth tokens encrypted at rest with `cryptography.fernet`. Key rotation supported (with a known UX cost — see [OPERATIONS.md](docs/OPERATIONS.md)).
- Audit log of every query, viewable per-user (members) or all (admins).

Full posture documented in [SPEC.md §9](SPEC.md#9-trust-posture).

## License

Apache License 2.0.

## Built by

[Swathi](https://github.com/SwathiMystery) for [Zingly](https://zingly.com), released as OSS so any company can run their own.
