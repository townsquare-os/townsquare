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

## Quickstart (self-host at your company)

```bash
# 1. Clone
git clone https://github.com/townsquare-os/townsquare
cd townsquare

# 2. Generate secrets
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,google,all]"
townsquare gen-secrets   # paste output into .env

# 3. Configure (Google Workspace OAuth credentials, Anthropic API key, your domain)
cp example.env .env
# edit .env

# 4. Up
cd docker && docker compose up -d

# 5. Visit http://localhost:8000
# Log in with your @yourcompany.com Google account
# Connect your Gmail / Drive / Calendar
# Ask a question
```

## What v0.1 ships

| Feature | Status |
|---|---|
| Google Workspace SSO with domain restriction | week 1 |
| Gmail / Drive / Calendar connectors | week 3 |
| Per-user encrypted OAuth token storage | week 1 |
| Federation router across users | week 4 |
| Central agent (Claude Agent SDK) | week 4 |
| HTMX + Tailwind web UI | week 2 |
| Postgres-backed wiki + lightweight CRM | week 5 |
| Docker Compose self-host | week 0 (done) |

See [ROADMAP.md](ROADMAP.md) for v0.2 / v0.3 / v0.4 plus directional v0.5+ ideas.

## Specification

townsquare is **spec-first**. The language-agnostic contract is in [SPEC.md](SPEC.md). The Python implementation in this repo is the reference; you can implement townsquare in any language by following the spec.

## Trust posture

- All data stays on your infrastructure. townsquare makes no outbound calls except to (a) the LLM provider you configure, and (b) the data sources each user connected.
- No telemetry. No phone-home. Apache 2.0 with explicit "no analytics" guarantee.
- Per-user isolation: Bob can never see Carol's data unless Carol's source-side permissions allow it.
- All OAuth tokens are encrypted at rest with `cryptography.fernet`. Key rotation supported.
- Audit log of every query for compliance.

Full posture documented in [SPEC.md §9](SPEC.md#9-trust-posture).

## License

Apache License 2.0.

## Built by

[Swathi](https://github.com/SwathiMystery) for [Zingly](https://zingly.com), released as OSS so any company can run their own.
