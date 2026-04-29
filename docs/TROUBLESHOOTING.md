# Troubleshooting

Common issues during self-host setup and operation. If yours isn't here, open an issue: https://github.com/townsquare-os/townsquare/issues

## Setup

### `redirect_uri_mismatch` when clicking "Sign in with Google"

**Cause:** the `Authorized redirect URIs` registered in Google Cloud Console don't match `GOOGLE_REDIRECT_URI` in `.env`.

**Fix:** they must match character-for-character. Common gotchas:

- `http://` vs `https://`
- Trailing slash (`/auth/google/callback/` vs `/auth/google/callback`)
- A different port (`:8000` vs no port)

Update one to match the other and redeploy.

### Login bounces back to the login page

**Cause #1:** the cookie isn't being set. Check that you're going through the reverse proxy correctly. If `RUNTIME_ENV=prod` then session cookies are `https_only`; without TLS the cookie is dropped silently.

**Fix:** either run with `RUNTIME_ENV=dev` for local testing, or set up TLS.

**Cause #2:** the Google `hd` claim or `email_verified` claim doesn't match.

**Fix:** the user must be a real Workspace user in your domain, not a `@gmail.com` personal account. Check `docker compose logs api` for `domain '...' not allowed` or `email_verified=false`.

### `FERNET_KEY is required`

**Cause:** `.env` doesn't have a `FERNET_KEY` set.

**Fix:** `make gen-secrets`, paste both lines into `.env`, restart with `make restart`.

### `invalid_client` from Google

**Cause:** the `GOOGLE_CLIENT_SECRET` has a stray character (whitespace, newline) or is the wrong secret.

**Fix:** recopy from Google Cloud Console → Credentials → your OAuth client. Re-paste cleanly.

## Operation

### Gmail / Drive returns no results when the user definitely has matching mail/files

**Cause #1:** the user revoked the grant. Check https://myaccount.google.com/permissions on their account.

**Cause #2:** the OAuth scopes weren't all granted at sign-in. Some users see Google's individual checkbox screen and uncheck Gmail or Drive.

**Fix:** have the user sign out (`/logout`) and sign back in. Tell them to leave all permission boxes checked.

**Cause #3:** rate-limited. Gmail and Drive each have per-user rate limits. Heavy fanout (every employee × every source × multiple queries) can hit them. Reduce `per_target_limit` in selector queries or add a small delay.

### `Anthropic 429` rate limit errors in the agent

**Cause:** your Anthropic account is on a low tier and the team is querying faster than the tier allows.

**Fix:** raise your Anthropic usage tier (https://console.anthropic.com/settings/limits). The Tier 2/3 limits are usually sufficient.

### Database connection failures on first start

**Cause:** the `db` container hasn't finished initialising before the api tried to connect.

**Fix:** docker-compose has a healthcheck on the db service that the api waits for. If you see this anyway, try `make rebuild`. The entrypoint also retries `init-db` at start.

### Out of memory

**Cause:** Postgres + the api together need ~700 MB minimum. Cheap droplets with 512 MB will OOM.

**Fix:** upgrade to a 1 GB droplet. Or run db separately on a managed Postgres.

### Slow queries (>30 s)

**Cause:** the federation router is fanning to a lot of (user, source) targets, and each Google API call adds latency. With 50 employees × 3 sources, that's 150 parallel API calls.

**Fix #1:** lower `per_target_concurrency` (default 8) is rarely the bottleneck; the bottleneck is *number* of targets. Use the agent's `users` or `sources` parameter to restrict the fanout when context is clear.

**Fix #2:** the v0.2 selector heuristics (calendar attendance, channel membership) will narrow this. Track at https://github.com/townsquare-os/townsquare/issues.

## Data

### Data deletion when an employee leaves

```bash
docker compose exec api townsquare admin deactivate alice@acme.com
```

Sets `is_active=false` on the user and on every connection. The federation router immediately stops including her data. Wiki pages she edited are preserved.

For full erasure (GDPR): `townsquare admin forget alice@acme.com`.

### Restoring from a backup

```bash
make restore FILE=backups/20260430T020000Z.sql.gz
```

This pipes the dump into `psql`. Don't restore on top of a live database that has new data — it'll fail on duplicate primary keys. Restore into a fresh / empty database.

## Development

### Tests fail with "no such table"

**Cause:** the `fresh_db` fixture drops + recreates tables. If you're not using it (e.g., a unit test doesn't depend on DB), and code paths reach the DB layer anyway, you'll get this.

**Fix:** add `fresh_db` to the test signature, or restructure the test to not touch DB.

### `ImportError: cannot import name '...' from 'townsquare.web.routes'`

**Cause:** circular import. `routes/auth.py` imports from `web.deps` which imports from `db` which imports from `db.engine` etc. Don't add cross-imports.

**Fix:** move the offending import inside the function body, or extract a helper module.
