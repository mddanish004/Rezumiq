# Rezumiq API

Django 5.2, django-allauth (email/password, Google), Postgres, the Tectonic LaTeX compiler, Cloudflare R2 storage,
Dodo Payments, and a React frontend talking to it over HTTP. Locally the API is at `http://localhost:8000` and the
Vite app at `http://localhost:5173`.

## Layout

```
server/
  manage.py            python-dotenv loads server/.env for every command
  rezumiq/             settings, urls, wsgi
  accounts/            custom user, health endpoints, dev guest login
  resumes/             resumes, versions, master profile, templates
  jobs/                saved job posts and AI parsing
  ats/                 rule-based ATS score, parser, AI match and review
  coverage/            requirement coverage against a parsed job
  imports/             PDF/text/LaTeX import and notes-to-draft
  pdfs/                preview and download compilation
  share_links/         public links and link views
  public/              public profile, resume, and PDF pages
  analytics/           link views by day, source, country, device
  billing/             Dodo checkout, subscriptions, refunds, webhooks
  admin/               staff-only product, AI, revenue, content, system data
  tests/               pytest (pytest-django)
  Dockerfile           production image, includes the Tectonic binary
```

## Run it locally

Needs Python 3.13 and Docker (or any Postgres).

```sh
python3.13 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env                 # set DATABASE_URL and DJANGO_SECRET_KEY
docker compose up -d                 # local Postgres, matches the default DATABASE_URL
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_templates
.venv/bin/python manage.py createsuperuser   # optional, for /admin
.venv/bin/python manage.py runserver
```

- Health: `GET /health` and `GET /health/deep` (database plus the Tectonic binary).
- Auth: allauth headless at `/_allauth/…` for the React app (signup, login, password reset), Google OAuth through
  the provider endpoints, and `POST /auth/guest` for a dev guest account (disabled when `DJANGO_DEBUG=false`).
- Django admin at `/admin/` for support work. The product control room is `/app/admin` in the frontend and needs an
  address in `ADMIN_EMAILS` **and** a verified email.
- Tectonic locally: `brew install tectonic`, or grab the static binary from
  [releases](https://github.com/tectonic-typesetting/tectonic/releases). Without it, `/health/deep` reports the
  compiler missing and PDF previews fail.
- Tests use `DATABASE_URL=sqlite:////tmp/…` so they never touch a real database:
  ```sh
  DATABASE_URL=sqlite:////tmp/opencode/test.sqlite3 .venv/bin/pytest -q
  ```

## Google sign in

Create an OAuth client (Web) in Google Cloud console. Add
`<API_URL>/accounts/google/login/callback/` as an authorized redirect URI. Locally that is
`http://localhost:8000/accounts/google/login/callback/`. Put the client id and secret in `.env`.

## Checks

```sh
.venv/bin/ruff check .
.venv/bin/pytest
```

## Production

The Dockerfile is the Render service image. The repository's root `render.yaml` defines the web service and the
daily maintenance cron. Apply it as a Blueprint in Render, then fill in every `sync: false` value. Render supplies
`PORT`; secrets come from the service's environment variables. Migrations run as the pre-deploy command, not at
boot:

```sh
python manage.py migrate --noinput
```

The container starts Gunicorn bound to `$PORT`. `/health` gates rollout and `/health/deep` backs the uptime job.
`RENDER_EXTERNAL_HOSTNAME` is added to `ALLOWED_HOSTS` automatically, so the default `onrender.com` host also works.

### Environment checklist

Copy `.env.example` and set at least:

| Variable | Notes |
| --- | --- |
| `DATABASE_URL` | Neon pooled connection string. |
| `DJANGO_SECRET_KEY` | Required when debug is off. Changing it invalidates sessions and reset links. |
| `DJANGO_DEBUG` | `false`. |
| `ALLOWED_HOSTS` | API host, e.g. `api.rezumiq.com`. |
| `FRONTEND_URL` | Public frontend origin. Share links, redirects, and auth email links use it. |
| `SMTP_HOST` and friends | Required; verification and password reset fail without mail. |
| `CORS_ALLOWED_ORIGINS` | Frontend origin(s), comma separated. |
| `CSRF_TRUSTED_ORIGINS` | Same origins. Defaults to `CORS_ALLOWED_ORIGINS`. |
| `COOKIE_DOMAIN` | Parent domain, e.g. `.rezumiq.com`, so the app and API share the session. Also the default for `CSRF_COOKIE_DOMAIN`, which the frontend reads from `document.cookie`. |
| `COOKIE_SAMESITE` | `Lax` for a shared parent domain. `None` only for unrelated domains, and it requires HTTPS. |
| `SECURE_HSTS_SECONDS` | HSTS max-age. Defaults to one year in production; set `0` while validating a domain. |
| `ADMIN_EMAILS` | Staff addresses for the control room. Verify the email after signup. |
| `AI_KEY_ENCRYPTION_SECRET` | Long random value. Keep it stable or stored BYOK keys stop decrypting. |
| `STORAGE_DRIVER` / `R2_*` | `r2` plus the account, bucket, and access keys for uploads and compiled PDFs. |
| `TECTONIC_ONLY_CACHED` | `true` in production; the image ships the cached bundle. |
| `GROQ_API_KEY` | Required for the free-tier AI flows. |
| `SENTRY_DSN` | Optional. Enables Sentry error reporting; `SENTRY_ENVIRONMENT` labels the events. |

### Dodo Payments

- Test mode and live mode have separate keys **and separate products**. The two test product ids do not work in
  live mode; create the Season Pass and Pro products again in live mode.
- Keep `DODO_ENVIRONMENT` matched to the key. A test key with `live_mode` will fail.
- Point the Dodo webhook at `<API_URL>/v1/webhooks/dodo`. Copy the endpoint secret into `DODO_WEBHOOK_KEY`
  (starts with `whsec_`).
- Locally, use `dodo wh listen` to forward events; a locally generated secret can verify the signature but cannot
  receive dashboard deliveries without a public URL.
- Refunds are asynchronous: `request_refund` reserves the payment, `refund.succeeded` finalizes it, and
  `refund.failed` releases the claim.

### Storage

`STORAGE_DRIVER=r2` stores uploads and compiled PDFs in Cloudflare R2. Set `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`,
`R2_SECRET_ACCESS_KEY`, and `R2_BUCKET`. The bucket stays private; the app reads objects through the API. With
`local`, files live under `server/storage/` and are lost when the container restarts.

### Deploy checklist

1. Apply the root `render.yaml` Blueprint in Render and fill in every `sync: false` value. It creates the web
   service and the daily maintenance cron.
2. Confirm the pre-deploy migration ran in the deploy log.
3. Run `python manage.py seed_templates` once (idempotent).
4. Confirm `/health/deep` reports `database: ok` and `compiler: ok`.
5. Add the deployed frontend origin to `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`.
6. Set `FRONTEND_URL` and redeploy the frontend with `VITE_API_URL` pointing at the API.
7. Create the live Dodo products, switch the key and environment, and register the webhook.
8. Sign in with an address in `ADMIN_EMAILS`, verify the email, then open `/app/admin`.
9. Compile one PDF and open one share link from a signed-out browser.
10. Confirm the maintenance cron has a successful run in Render's cron history.

### Operations

- Gunicorn reads `WEB_CONCURRENCY` (default 2), `GUNICORN_THREADS` (default 2), and `GUNICORN_TIMEOUT`
  (default 120s) from the environment.
- The blueprint schedules `python manage.py run_maintenance` daily at 03:00 UTC on the same image and environment.
  It expires subscriptions, prunes old uploads and deleted resumes, and purges stale guests.
- Public ATS allows 20 requests/min per IP; share password guesses allow 10 failures per link per 10 minutes.
  Allauth limits login, signup, and password reset. These counters use Django's cache, which is per process
  in the default configuration; point `CACHES` at Redis if several instances must share one budget.
- `.github/workflows/uptime.yml` checks `/health/deep` every 30 minutes once the API is live; a failed run
  notifies the repository maintainers.
- Set `SENTRY_DSN` to capture unhandled errors and 500 logs; without it, they only reach the Render logs.

### Secrets

- `.env` is ignored; `.env.example` only has empty placeholders. Do not put real keys in tracked files.
- Rotate any provider key that has ever been committed or pasted into a ticket, even a test-mode key.
- Back up the database before a migration that touches billing or usage rows.
