# Self-hosting townsquare

This guide takes you from "fresh git clone" to "everyone at your company is signed in and asking questions" in about 30 minutes of focused work.

## What you need before starting

Mandatory:

- **A Google Workspace** for your company (the free trial works for small teams).
- **A Linux host** with Docker + Docker Compose. Anything will work — a $6 DigitalOcean droplet, an EC2 t3.small, a server in your office. Allow 1 GB RAM minimum, 2 GB recommended.
- **A DNS name** you control, pointing at the host (e.g. `townsquare.acme.com`). You'll need TLS — Caddy or a managed proxy is easiest.
- **An Anthropic API key** ([console.anthropic.com](https://console.anthropic.com)). Set up billing; expect ~$5–$50/month at small-team scale.

Optional:

- A reverse proxy (Caddy, nginx, Cloudflare Tunnel). Not strictly required for local-network use; required for public TLS.

## Architecture you're standing up

```
                 ┌──────────────────────────────────────┐
                 │           townsquare.acme.com        │
                 │                                      │
                 │      Reverse proxy (Caddy/nginx/CF)  │
                 │                  ↓                   │
                 │           api container             │
                 │      (FastAPI + Anthropic)           │
                 │                  ↕                   │
                 │           db container              │
                 │      (Postgres + pgvector)           │
                 │                                      │
                 └──────────────────────────────────────┘
                                 ↕
              Google Workspace OAuth (per-user creds)
              Google Gmail / Drive / Calendar APIs
              Anthropic API
```

Everything except outbound calls to Google + Anthropic stays on your host.

---

## Step 1 — Clone and prepare secrets (5 min)

```bash
git clone https://github.com/townsquare-os/townsquare
cd townsquare
cp example.env .env
```

Generate cryptographic secrets:

```bash
docker compose run --rm api townsquare gen-secrets
```

This prints two lines:

```
FERNET_KEY=...
SECRET_KEY=...
```

Paste them into `.env`. **Do not commit `.env` to source control.** It's already in `.gitignore`.

---

## Step 2 — Set up Google Workspace OAuth (10 min)

This is the fiddliest step. Follow [docs/GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md) carefully — the **OAuth consent screen User Type = Internal** decision is what avoids Google's app verification dance.

You'll come away with:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- A configured redirect URI: `https://townsquare.acme.com/auth/google/callback`

Add these to `.env`:

```ini
GOOGLE_CLIENT_ID=123456789-xxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxx
WORKSPACE_DOMAIN=acme.com
GOOGLE_REDIRECT_URI=https://townsquare.acme.com/auth/google/callback
```

**Important:** `WORKSPACE_DOMAIN` enforces server-side that *only* `@acme.com` Google accounts can sign in. Any other Google account will be rejected even if they make it through the OAuth flow.

---

## Step 3 — Add the Anthropic key (1 min)

```ini
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-sonnet-4-6
```

---

## Step 4 — Boot the stack (1 min)

```bash
docker compose up -d --build
docker compose logs -f api
```

You should see:

```
[townsquare] initialising database...
Initialised tables at postgresql+psycopg://townsquare:***@db:5432/townsquare
[townsquare] starting server on 0.0.0.0:8000
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Health check:

```bash
curl http://localhost:8000/healthz
# {"status":"ok","version":"0.1.0"}
```

---

## Step 5 — Put it behind TLS (5 min)

townsquare must be reachable at the same `GOOGLE_REDIRECT_URI` you registered with Google. For production that means HTTPS.

### Caddy (recommended — auto Let's Encrypt)

`/etc/caddy/Caddyfile`:

```
townsquare.acme.com {
    reverse_proxy localhost:8000
}
```

```bash
sudo systemctl reload caddy
```

Caddy auto-provisions a TLS cert on first request. That's it.

### Cloudflare Tunnel (no public IP needed)

```bash
cloudflared tunnel create townsquare
cloudflared tunnel route dns townsquare townsquare.acme.com
cloudflared tunnel --config config.yml run
```

Set `service: http://localhost:8000` in the tunnel config.

### nginx (if you already run it)

```nginx
server {
    listen 443 ssl http2;
    server_name townsquare.acme.com;
    # ssl_certificate ...;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Step 6 — Sign in and promote yourself to admin (2 min)

1. Open `https://townsquare.acme.com` in your browser.
2. Click **Sign in with Google**. Use your `@acme.com` account.
3. After the redirect lands you back on the dashboard, you're a regular member. Promote yourself:

```bash
make admin-list-users
# verify your email appears

docker compose exec api townsquare admin promote you@acme.com
# Promoted you@acme.com to admin.
```

---

## Step 7 — Onboard the rest of the team (5 min)

Tell your colleagues: visit `https://townsquare.acme.com`, sign in with Google. That's it. Each person's Gmail / Drive / Calendar is connected automatically with their own credentials at sign-in time.

Visit `/connections` to verify what each user has connected. Visit `/` to ask the first question.

---

## Operations

### Backups

The Postgres volume holds *all* user data (encrypted OAuth tokens, query logs, wiki, CRM). Back it up nightly.

```bash
make backup                                # writes ./backups/<UTC stamp>.sql.gz
make restore FILE=backups/20260430T020000Z.sql.gz
```

To automate via cron:

```cron
0 2 * * * cd /opt/townsquare && make backup >> /var/log/townsquare-backup.log 2>&1
```

Off-site: rsync `./backups/` to S3 / B2 / a second host.

### Logs

```bash
make logs                          # tail api
docker compose logs -f db          # tail db
```

### Updating to a new version

```bash
git pull
make rebuild
```

The entrypoint reruns `init-db` on every start, which is idempotent — schema migrations apply automatically.

### Restart

```bash
make restart   # api only — fastest
```

### When an employee leaves

```bash
docker compose exec api townsquare admin deactivate alice@acme.com
# Their connections become inactive; their data stops being federated immediately.
```

For a full GDPR-style erasure (delete the user row, all connections, all query logs):

```bash
docker compose exec api townsquare admin forget alice@acme.com
```

Wiki pages they created or edited are **preserved** (those belong to the company, not the individual).

### Rotating secrets

If you suspect a token leak:

1. Generate fresh `SECRET_KEY` and `FERNET_KEY` with `make gen-secrets`.
2. **Caveat**: rotating `FERNET_KEY` invalidates every stored OAuth token. Every user must sign in again to re-grant. There's no way around this — that's the whole point of encryption-at-rest.
3. Restart: `make restart`.

### Tear-down

```bash
docker compose down              # stops, keeps data
docker compose down -v           # stops + DELETES the database (DANGER)
```

---

## Cost expectations

| Component | Typical monthly cost |
|---|---|
| Host (DigitalOcean droplet, 2 GB) | $12 |
| Anthropic Claude Sonnet 4.6 (~30 queries/day at ~5k tokens each across a 10-person team) | $30 – $80 |
| Domain + TLS (Let's Encrypt) | ~$10/year for the domain |
| **Total** | **~$45 – $95 / month** |

Tune via `PER_USER_QUERY_BUDGET_USD_DAILY` and `PER_QUERY_TOKEN_CAP` in `.env`.

---

## Trust posture

A self-hosted townsquare instance:

- Stores all user data on **your** infrastructure. The only outbound calls are:
  - Anthropic API (your API key, configurable)
  - Google API (each user's own access token, scoped to that user)
- Encrypts all OAuth tokens at rest with `cryptography.fernet` (AES-128-CBC + HMAC-SHA256).
- Sends no telemetry. No phone-home. No analytics.
- Isolates per-user permissions: bob@acme.com can never see carol@acme.com's data unless Google's source-side ACL allows it.

If you need to provide a security review document to your CISO, point them at [SPEC.md §9 (Trust posture)](../SPEC.md#9-trust-posture) and the source code under `src/townsquare/auth/`. Everything is auditable.

---

## What v0.1 does *not* include

Be honest with stakeholders about scope:

- **No Slack / Notion / GitHub yet** — coming in v0.2 (see [ROADMAP.md](../ROADMAP.md)).
- **No SAML SSO** — Google Workspace only at v0.1.
- **No multi-tenant SaaS** — one instance per company.
- **No on-call alerts / Grafana dashboards** — bring your own (logs are structured stderr).
- **No vector search yet** — connectors use the source's native search (Gmail's, Drive's, Calendar's).

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for the common failure modes:

- "redirect_uri_mismatch" from Google
- "FERNET_KEY is required"
- The login button bounces back to login
- The API can't reach the DB
- Anthropic 429 rate-limit
- Gmail returning 403 even after grant

If you hit something not in there, open an issue at https://github.com/townsquare-os/townsquare/issues with the `[support]` label.
