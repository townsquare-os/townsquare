# townsquare Service Specification

**Status:** Draft v1 (language-agnostic)

**Purpose:** Define a self-hostable company OS that uses Google Workspace
SSO, lets each employee connect their own data sources, and federates
queries across users with privacy enforced at the source.

The reference implementation is Python (`pip install townsquare`). Other
implementations MAY be written in any language by conforming to the
contracts below.

## Normative Language

`MUST`, `MUST NOT`, `REQUIRED`, `SHOULD`, `SHOULD NOT`, `RECOMMENDED`,
`MAY`, `OPTIONAL` follow RFC 2119.

## 1. Problem Statement

Companies want a brain that knows everything. Existing options either
centralise everyone's data through a service account (privacy nightmare)
or hand the brain to a third-party SaaS (control nightmare).

townsquare solves this by:

1. Self-hosting everything. No third-party UI, no third-party auth, no
   data leaving the company's infrastructure beyond the LLM provider.
2. Authenticating each user via the company's existing Google Workspace.
3. Letting each user connect their own data sources with their own
   OAuth credentials.
4. Federating queries across users so privacy is enforced at the source.

## 2. Goals and Non-Goals

### 2.1 Goals

- Self-hostable in one Docker Compose command.
- Google Workspace SSO with domain restriction.
- Per-user OAuth data connections (Gmail, Drive, Calendar at v0.1).
- Federated query plane that respects per-user permissions at the source.
- Org-level shared brain (wiki, CRM).
- LLM-pluggable.
- Apache 2.0.

### 2.2 Non-Goals

- Multi-tenant SaaS in v0.1.
- Replacing source-of-record systems.
- Building yet another wiki software (small built-in only).
- Voice/audio integration in v0.1.

## 3. Architecture

```
                 ┌────────────────────────────────────┐
                 │  townsquare-server                 │
   Browser ─────▶│  ─ Google Workspace SSO            │
                 │  ─ Federation router               │
                 │  ─ Central agent                   │
                 │  ─ Shared brain (wiki, CRM)        │
                 │  ─ Web UI                          │
                 └─────────────┬──────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       Alice's tokens   Bob's tokens    Carol's tokens
       (encrypted)      (encrypted)     (encrypted)
              │                │                │
              ▼                ▼                ▼
       Alice's Gmail    Bob's Drive     Carol's Calendar
```

In v0.1 the per-user "sidecar" is logical, not physical. v0.3+ MAY
use isolated sidecar processes per user.

## 4. Core Domain Model

### 4.1 User
- `email`, `domain`, `name`, `role` ∈ {member, admin}, `is_active`, timestamps.

### 4.2 Connection
- `user_email`, `source` ∈ {gmail, drive, calendar, slack, ...}
- `oauth_token_encrypted`, `refresh_token_encrypted`, `granted_scopes`
- `is_active`, timestamps.

### 4.3 Query
- `id`, `user_email`, `query_text`, `selected_users`, `selected_sources`
- `latency_ms`, `tokens_used`, `cost_usd`, `created_at`.

### 4.4 Wiki Page
- `slug`, `title`, `body_markdown`, `created_by`, `last_edited_by`,
  `last_edited_at`, `version`.

### 4.5 CRM (fixed schema in v0.1)
- `deals`, `contacts`, `accounts`.

## 5. Authentication

### 5.1 Google Workspace SSO
- MUST use OAuth 2.0 Authorization Code with PKCE.
- MUST set `hd=<domain>` AND verify `hd` claim server-side.
- MUST verify `email_verified` is true.
- MUST reject mismatched-domain users.

### 5.2 Per-user OAuth tokens
- MUST be encrypted at rest with authenticated encryption.
- Encryption key MUST come from environment.
- Key rotation MUST be supported.

### 5.3 Trust gate
- MUST log every query and per-source fetch.
- Admins MAY view all logs; non-admins only their own.

## 6. Federation

### 6.1 Selector
- Returns ordered (user, source) targets.
- Default: all active users in domain; refined by metadata heuristics.

### 6.2 Fanout
- MUST execute targets in parallel.
- Per-target failures MUST NOT break the overall query.
- Each per-target query runs under that user's encrypted tokens.

### 6.3 Aggregation
- Results MUST carry per-user-per-source attribution.
- Final synthesis MUST cite (source, user_email) for each fact.

## 7. Connectors

A connector implements:
```
class Connector:
    source_id: str
    required_scopes: list[str]
    supports_update: bool
    async def search(query, access_token, limit) -> list[Item]
    async def fetch(item_id, access_token) -> Item | None
```

v0.1 ships: gmail, drive, calendar.
v0.2 adds: slack, notion, github.

## 8. Shared brain

Wiki and CRM accessible via agent tools. Wiki edits MUST be versioned.
v0.1 CRM uses fixed schema in §4.5; v0.3 MAY introduce schema-on-demand
with admin guardrails.

## 9. Trust posture

A townsquare-conformant implementation MUST document:
- All outbound destinations (LLM provider + connected sources only).
- Encryption-at-rest approach for OAuth tokens.
- Data retention policy for query logs.
- Data deletion procedure when a user leaves.

## 10. Compliance

A "townsquare-compatible" implementation MUST conform to all `MUST` in
§5, §6, §7, §9. The reference Python implementation is canonical.

## 11. Versioning

Semantic versioning. Current spec: **0.1.0** (Draft v1).
