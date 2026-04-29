# Google Workspace OAuth Setup

Step-by-step walkthrough to create the OAuth client townsquare needs.
Takes about 10 minutes. Do this **once** per company.

## What you'll end up with

- A `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` for your `.env`
- An OAuth consent screen marked **Internal** so only your `@acme.com` users can sign in (no Google verification dance required)
- The Gmail, Drive, Calendar APIs enabled on the project

## Prerequisites

- You're a Google Workspace **super-admin** at your company, OR you have permission to create OAuth apps
- You have a Google Cloud Console project (create one if not — it's free)

---

## Step 1 — Create or select a Google Cloud project

Go to https://console.cloud.google.com → top-bar project picker → **New Project**.

- **Project name:** `townsquare-acme` (anything memorable)
- **Organisation:** select your Google Workspace org

Hit **Create**. Wait ~15 seconds for it to provision. Switch to it via the top-bar picker.

---

## Step 2 — Enable the APIs townsquare uses

In the left nav: **APIs & Services → Library**. Enable each of:

1. **Gmail API**
2. **Google Drive API**
3. **Google Calendar API**

(For each: search the name → click → **Enable**.)

> No need to enable "Google+ API" or anything else. Just those three.

---

## Step 3 — Configure the OAuth consent screen (the critical step)

Left nav: **APIs & Services → OAuth consent screen**.

### User Type: **Internal**

This is the single most important choice in this entire guide. **Internal** means only users in your Google Workspace can authenticate. Google does not require app verification (no "verify your domain" / "submit screencast" / wait-7-days-for-review nonsense). The trade-off is you cannot let users from other domains sign in — which is exactly what you want for a single-tenant company OS.

Click **Internal** → **Create**.

### App information

- **App name:** `townsquare`
- **User support email:** your address
- **App logo:** optional (skip for now)
- **Application home page:** `https://townsquare.acme.com` (your deployed URL)
- **Authorized domains:** `acme.com` (your Workspace domain)
- **Developer contact:** your address

Click **Save and continue**.

### Scopes

Click **Add or remove scopes**. Search for and tick:

- `openid`
- `.../auth/userinfo.email`
- `.../auth/userinfo.profile`
- `.../auth/gmail.readonly`
- `.../auth/drive.readonly`
- `.../auth/calendar.readonly`

Click **Update** → **Save and continue**.

### Test users

Skip — Internal apps don't need test users. Click **Save and continue**.

### Summary

Review and click **Back to dashboard**.

---

## Step 4 — Create the OAuth client credentials

Left nav: **APIs & Services → Credentials → + Create credentials → OAuth client ID**.

- **Application type:** **Web application**
- **Name:** `townsquare`

### Authorized JavaScript origins

Add your deployed origin:

```
https://townsquare.acme.com
```

For local development add:

```
http://localhost:8000
```

### Authorized redirect URIs

This MUST exactly match what townsquare expects. Add:

```
https://townsquare.acme.com/auth/google/callback
```

For local development also add:

```
http://localhost:8000/auth/google/callback
```

> Trailing slashes matter. No trailing slash above.

Click **Create**.

A modal pops up showing your **Client ID** and **Client secret**. Copy both. (You can also retrieve them later from the credentials page.)

---

## Step 5 — Paste into `.env`

```ini
GOOGLE_CLIENT_ID=123456789-xxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxx
WORKSPACE_DOMAIN=acme.com
GOOGLE_REDIRECT_URI=https://townsquare.acme.com/auth/google/callback
```

---

## Step 6 — Test

```bash
docker compose up -d --build
```

Open `https://townsquare.acme.com`. Click **Sign in with Google**. You should:

1. Be redirected to Google's consent screen
2. See a list of permissions: Gmail (read), Drive (read), Calendar (read)
3. Click Allow → land back on `townsquare.acme.com/`

If you get `redirect_uri_mismatch`, double-check the URI in step 4 exactly matches `GOOGLE_REDIRECT_URI` in `.env`.

If a non-`@acme.com` user tries to sign in, they'll see Google's "your administrator hasn't given you access to this internal app" error before townsquare even sees the request. That's the Internal user type doing its job.

---

## When OAuth tokens expire

Google rotates access tokens every hour. townsquare stores the refresh token (from `access_type=offline` in the OAuth flow) which lets it mint new access tokens silently without user re-consent.

For Workspace **Internal** apps, refresh tokens **do not expire** unless:

- The user revokes the grant manually at https://myaccount.google.com/permissions
- An admin revokes it via the Workspace admin console
- The user's Workspace account is deleted

So in normal operation, users never need to re-sign-in. If they do, just have them log in again — townsquare will refresh their stored connection.

---

## Common mistakes

| Symptom | Cause | Fix |
|---|---|---|
| `redirect_uri_mismatch` | URI in `.env` doesn't match the registered URI exactly | Match them character-for-character (trailing slashes, http vs https) |
| User on `@gmail.com` makes it through | OAuth client was created with **External** user type | Recreate as **Internal**. Domain restriction in townsquare also catches this server-side as defence in depth |
| `access_denied` | User declined a scope on the consent screen | They must accept all 6 scopes for connectors to work |
| `invalid_client` | Client secret doesn't match | Recopy from the Credentials page; check for hidden whitespace |
| No refresh token returned | OAuth client config didn't request `access_type=offline` (townsquare does — but Google sometimes drops it on re-grant) | Have the user revoke at myaccount.google.com/permissions then sign in fresh |
