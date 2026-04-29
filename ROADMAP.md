# townsquare Roadmap — 10 weeks from scaffold to first deployment to OSS launch

This is a living document. Weeks slide based on real progress.

## Week 0 — Scaffold (DONE)

- Repo at `~/repos/townsquare/`
- `pyproject.toml`, README, ROADMAP, SPEC, LICENSE, CONTRIBUTING in place
- Module skeleton imports cleanly; smoke tests green
- CI workflow draft
- Decision: name = `townsquare`; org = `townsquare-os`

## Week 1 — Auth + identity

- Google Workspace SSO via OAuth 2.0 (Authlib)
- Domain restriction enforced server-side (`hd` param + verified email)
- User auto-provisioning on first SSO
- Server-side sessions (itsdangerous)
- Token encryption at rest (cryptography.fernet)
- Postgres schema applied via Alembic migration
- Login/logout flow end-to-end working

## Week 2 — Web UI shell

- HTMX + Jinja + Tailwind
- Pages: login, dashboard, connections, query, wiki, settings
- Mobile-friendly responsive layout
- Basic styling polish

## Week 3 — Google connectors

- Gmail (search, body, header parsing)
- Drive (search files, fetch text from Docs/Sheets/Slides)
- Calendar (search events, attendees, recurring meetings)
- Per-user OAuth scope granted at SSO time (no extra dance)
- Connection management UI

## Week 4 — Federation router + central agent

- Router with parallel fanout (asyncio.gather, bounded concurrency)
- Default selector: domain-wide; refinement: calendar/channel heuristics
- Central agent using Claude Agent SDK
- Tools: `query_user_gmail`, `query_user_drive`, `query_user_calendar`,
  `query_wiki`, `update_wiki`, `query_crm`, `update_crm`
- Streaming responses to the UI
- Per-source response cache (Postgres-backed TTL)

## Week 5 — Shared brain (wiki + CRM)

- Postgres-backed wiki: pages, history, edit-in-browser, markdown
- Optional Git-backed wiki sync
- CRM: deals, contacts, accounts (fixed schema in v0.1)
- Glossary: org-defined terms
- Agent tools wired

## Week 6 — Slack + GitHub + dogfood prep (DONE — 2026-04-29)

- Slack OAuth (per-user xoxp user-token, not bot-token, for per-user privacy)
- `query_user_slack`: search messages, threads, DMs (only the user's)
- GitHub via fine-grained PAT (per-user)
- `query_user_github`: search issues + PRs in repos the user can see
- Connect/disconnect UI flows for both
- Re-deploy to first-deployment staging
- Onboard 3 alpha users at the first deployment

## Week 7 — Soft launch at first deployment

- Onboard the rest of the team at the first deployment
- Production monitoring
- Performance tuning (query latency p95 target: < 5 s)
- Bug fixes from alpha feedback
- README polished with screenshots

## Week 8 — Go-live + v0.1.0 release

- Everyone at the first deployment actively using townsquare
- v0.1.0 tagged on GitHub; PyPI release
- Internal case study written

## Weeks 9–10 — Public OSS launch

- Notion + GitHub connectors
- X thread quote-tweeting Scout / Glean
- Show HN
- dev.to launch post
- Goal: first 5 alpha-user companies recruited from launch

---

## v0.2 (post-launch, 4–6 weeks)

- OpenTelemetry instrumentation
- Helm chart for k8s
- Linear / Jira / Asana connectors
- Better selector heuristics (graph-aware)
- Per-user rate limits and budgets
- Audit log UI for compliance review

## v0.3

- True per-user sidecar processes (one container per user)
- BYO LLM: Ollama / vLLM / Bedrock providers
- Schema-on-demand CRM with strict guardrails
- Approval workflow for `update_*` tools

## v0.4

- Multi-tenant SaaS mode
- Privacy-aware analytics
- SOC 2 friendly compliance reports
- SAML SSO (in addition to Google Workspace)

## Directional / not committed

### Voice integration (with hummem)

Voice agents could query townsquare for caller context, sub-300 ms,
via hummem. "Voice agent reaches into the company brain at <300 ms."

### A2A protocol

When the Linux Foundation A2A protocol stabilises, expose townsquare's
agent as an A2A endpoint for cross-company agent interop.

### Per-employee LLM choice

Different employees have different LLM preferences (privacy, cost). Let
each user pick their own LLM for their own queries.
