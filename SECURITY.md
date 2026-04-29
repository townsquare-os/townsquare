# Security Policy

townsquare handles sensitive data — employees' OAuth tokens, query history,
shared wiki content. We take security reports seriously and respond promptly.

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please report privately via either:

1. **GitHub Security Advisories** — preferred. Go to the repository's
   **Security** tab → **Advisories** → **Report a vulnerability**.
2. **Email** the maintainers (see commit log for current maintainers' git
   emails).

Include:

- A clear description of the issue
- Steps to reproduce
- The version (`townsquare version` or commit SHA) you tested against
- The potential impact

We will acknowledge receipt within **48 hours** and aim to publish a fix or
mitigation within **14 days** for high-severity issues.

## Supported versions

We patch security issues on the latest released minor version. Older minor
versions receive patches only for critical issues, and only for 90 days
after a newer minor is released.

| Version | Supported |
|---|---|
| 0.1.x | ✓ |

## Scope

In scope:

- Authentication / authorisation flaws (SSO bypass, session hijack, token
  decryption)
- Injection (SQL, command, header)
- SSRF / RCE
- Secrets leakage
- Data exposure across users (the federation router must never let user A
  see user B's source data without user B's source-side permission)
- Cryptographic weakness in token-at-rest encryption

Out of scope:

- Denial-of-service via Anthropic API rate limits (configurable budgets exist
  for this)
- Issues requiring physical access to the host
- Social engineering of operators
- Issues in third-party dependencies that aren't yet patched upstream (please
  report those upstream first)

## Disclosure timeline

We follow a 90-day coordinated disclosure window from receipt of report. If a
fix lands sooner, the advisory is published immediately. If we need more
time, we will tell you and explain why.

## Trust posture

See [SPEC.md §9](SPEC.md#9-trust-posture) for the architectural guarantees
that townsquare is designed to provide.
