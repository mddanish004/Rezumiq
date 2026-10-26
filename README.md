# Rezumiq

An AI resume builder for students and professionals in every field, from software and data to banking, finance,
consulting, marketing and design. Write a resume in a form or in LaTeX, tailor it to a job post with AI, download a
real LaTeX PDF, and share it with a link that tells you who opened it.

This repository is a rewrite of the open source project [Shortlist](https://github.com/srvjha/shortlist) (MIT),
rebuilt on a new stack under the name Rezumiq: a Django API and a React + Vite app.

## Repository

| Folder    | What it is                                                                                                                    |
| --------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `server/` | The API: Django, Django ORM on Postgres, django-allauth (email/password + Google), Tectonic LaTeX, Cloudflare R2, Dodo Payments |
| `frontend/` | The React + Vite + TypeScript + Tailwind app: landing, auth, dashboard, editors, import, ATS, sharing, analytics, profile, billing, usage, settings, and the admin control room |

## Feature scope of the rewrite

- Two editors: a form editor and a LaTeX editor with live compile errors, 14 templates grouped by field, spacing and
  font presets.
- Import from PDF, LaTeX or pasted text, read in by AI with rule-based repair on the same file.
- AI tailoring against a pasted job post or URL, every change shown for review before it applies.
- Rule-based ATS score out of 100, in the editor and on a public page.
- Immutable version history per resume, with conflict protection between two tabs.
- Public share links with view analytics, optional password, expiry and contact hiding.
- Email/password and Google sign in, plus guest accounts in development.
- Plans: a free tier and two paid AI tiers, billed with Dodo Payments.
- Admin control room for product numbers, users, AI cost, revenue, content, and system health.

## Deploy plan

The API runs on Render (Docker service, migrations on release). The frontend runs on Vercel. The database is Postgres
(Neon in production), uploads and compiled PDFs live in Cloudflare R2, and payments run through Dodo. CI lives in
`.github/`.

## Run it locally

See [server/README.md](server/README.md) and [frontend/README.md](frontend/README.md). The production checklist,
environment variables, Dodo live-mode notes, and CORS/cookie rules live in the server README.
