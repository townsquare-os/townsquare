# Operations

Day-2 reference for running townsquare in production. For initial setup see [SELF_HOSTING.md](SELF_HOSTING.md).

## Routine

| Task | Command |
|---|---|
| Tail api logs | `make logs` |
| Restart api | `make restart` |
| Rebuild api after code change | `make rebuild` |
| Backup database | `make backup` |
| List users | `make admin-list-users` |

## Admin CLI cheatsheet

All run via `docker compose exec api townsquare admin <subcommand>`.

```bash
townsquare admin list-users              # show every registered user

townsquare admin promote you@acme.com    # grant admin role
townsquare admin demote alice@acme.com   # revoke admin role

townsquare admin deactivate bob@acme.com # employee leaves — soft delete
townsquare admin forget bob@acme.com     # GDPR-style hard erase
```

## Backups

`make backup` writes `./backups/townsquare-<UTC stamp>.sql.gz`. The dump includes:

- All users and their **encrypted** OAuth tokens
- All connections
- All query logs
- The wiki and CRM tables

It does **not** include your `.env` file or the encryption key. **You must back those up separately and keep them somewhere safe.** Without `FERNET_KEY` you cannot decrypt the OAuth tokens in the backup, even though you have the dump — by design.

### Recommended: nightly cron + off-site

```cron
# /etc/cron.d/townsquare-backup
0 2 * * * root cd /opt/townsquare && /usr/bin/make backup >> /var/log/townsquare-backup.log 2>&1
30 2 * * * root rsync -az /opt/townsquare/backups/ s3://acme-backups/townsquare/
```

Retain ~30 days locally; longer off-site.

## Upgrading

```bash
git pull
make rebuild
```

The container's entrypoint reruns `init-db` on every start. Schema additions are applied idempotently.

For breaking changes (rare in v0.x), check the release notes at https://github.com/townsquare-os/townsquare/releases before pulling.

## Monitoring

v0.1 ships **no built-in monitoring**. The recommendations:

- **Health check:** Hit `/healthz` from your existing uptime monitor (UptimeRobot, BetterStack, etc.). Returns `{"status":"ok","version":"..."}`.
- **Logs:** uvicorn writes structured stderr. Pipe `docker compose logs` into your existing log shipper (Loki, Datadog, New Relic).
- **Errors:** wrap with Sentry by setting `SENTRY_DSN` (v0.2 will add native support; for v0.1 patch the FastAPI app to add `sentry_sdk.init` if needed).

v0.2 will add OpenTelemetry tracing.

## Rotating secrets

### `SECRET_KEY` (session signing)

Safe to rotate. Logs every active user out (their session cookies become invalid). Steps:

```bash
make gen-secrets       # take only the SECRET_KEY line
# update .env
make restart
```

### `FERNET_KEY` (OAuth token encryption)

**Disruptive.** All stored OAuth tokens become un-decryptable. Every user must sign in again to re-grant. There is no way around this — that's the whole point of encryption-at-rest.

```bash
make gen-secrets       # take only the FERNET_KEY line
# update .env
docker compose exec db psql -U townsquare townsquare \
  -c "UPDATE connections SET is_active = false;"
make restart
# Notify users to sign in again.
```

### `GOOGLE_CLIENT_SECRET`

Rotate when you suspect the secret leaked. Generate a new one in Google Cloud Console, paste into `.env`, `make restart`. No user impact — Authlib will pick up the new secret on the next OAuth flow.

### `ANTHROPIC_API_KEY`

Rotate via Anthropic console. Update `.env`, `make restart`.

## Performance tuning

### Per-user query budget

Each query fans out across (users × sources). At 50 employees × 3 sources, a single agent step is 150 parallel HTTP calls. The agent typically runs 2–4 steps. Total: 300–600 outbound API calls per question.

To cap costs, set in `.env`:

```ini
PER_USER_QUERY_BUDGET_USD_DAILY=2.0
PER_QUERY_TOKEN_CAP=30000
```

### Postgres tuning

For >50 employees, set in your Postgres config (or via PGTUNE):

```
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
work_mem = 16MB
```

Hot-table vacuum is automatic via the default autovacuum.

### API container

Default uvicorn runs single-process. For >100 employees, switch to gunicorn with multiple workers:

```dockerfile
CMD ["gunicorn", "townsquare.web.app:app", "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "4", "-b", "0.0.0.0:8000"]
```

## Network posture

By default `docker-compose.yml` only exposes:

- API on `${HOST_PORT:-8000}` (proxy this through TLS)
- Postgres on `127.0.0.1:5432` (bound to localhost only — for backup tooling)

If you don't need Postgres reachable from the host, comment out the `db` service's `ports:` block. The `api` container reaches `db` over the private docker network either way.

## Disaster recovery

### Lost the FERNET_KEY

If you lose the encryption key, you lose every stored OAuth token. The user data isn't gone, but you cannot decrypt the tokens to use them.

**Recovery:** restore the database from a backup that predates the key loss, OR mark all connections inactive and have every user re-sign-in. There's no third option — that's encryption working as designed.

### Database corruption

```bash
docker compose down
# Spin up a fresh db volume
docker volume rm townsquare_townsquare-pgdata
docker compose up -d --build
make restore FILE=backups/<latest>.sql.gz
```

### Whole-host loss

Your `.env` (with secrets) is the single point of recovery. Keep an encrypted copy somewhere safe (1Password, Bitwarden, AWS Secrets Manager).

To restore on a fresh host:

```bash
git clone https://github.com/townsquare-os/townsquare
cd townsquare
# Restore .env from your password manager
docker compose up -d --build
make restore FILE=<latest backup>
```

## Security checklist

Before declaring "in production":

- [ ] `RUNTIME_ENV=prod` in `.env`
- [ ] HTTPS only — no plain-HTTP access
- [ ] `SECRET_KEY` is 32+ bytes of randomness (`make gen-secrets` does this)
- [ ] `FERNET_KEY` is set and stored off-host in a password manager
- [ ] Postgres port is **not** publicly reachable
- [ ] Firewall allows only 80/443 from outside (and 22 from your bastion)
- [ ] Backups are running and restoring successfully (test the restore at least once)
- [ ] OAuth consent screen User Type = **Internal** in Google Cloud Console
- [ ] `WORKSPACE_DOMAIN` matches your Workspace exactly
- [ ] Anthropic API key has spend cap configured
