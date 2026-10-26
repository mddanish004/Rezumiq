# Rezumiq frontend

React, Vite, TypeScript, and Tailwind for the Rezumiq resume studio. The API lives in `../server/` and is
expected at `http://localhost:8000` during development.

## Run

```sh
cp .env.example .env       # VITE_API_URL, defaults to localhost:8000
pnpm install
pnpm dev                   # http://localhost:5173
```

The Django API must allow the frontend origin. Its `.env` already includes
`CORS_ALLOWED_ORIGINS=http://localhost:5173` and the same value in `CSRF_TRUSTED_ORIGINS`.
In production, add the deployed origin to both lists. If the frontend and API are on unrelated
domains, set `COOKIE_SAMESITE=None` on the API and serve both over HTTPS.

## Checks

```sh
pnpm typecheck
pnpm build
npx playwright test        # needs the API on :8000 and Vite on :5173
```

The Playwright smoke covers the landing page, signup with CSRF and session cookies, the empty
dashboard, resume creation and editing, version history, the AI drawer, LaTeX mode, import, profile
autosave, the saved ATS report, share links, the public resume and profile pages, analytics, the
public ATS report, usage, billing, and settings, in desktop and mobile viewports.

## Layout

```
src/
  components/     shared UI, editor, resume document, share dialog, public chrome, app shell
  pages/          landing, auth, legal, app screens, public profile and resume
  lib/api.ts      typed fetch client for /v1, public share endpoints, and allauth headless
  lib/resume.ts   resume content types, normalization, and small helpers
  lib/auth.tsx    session context and protected routes
```

The UI follows the attached design reference: warm paper, ink, one lime accent, editorial serif display,
and mono metadata.

Implemented so far:

- Landing, authentication, app shell, dashboard, resumes, import, jobs, ATS, analytics, profile, usage,
  billing, and settings.
- Structured resume editor with basics, experience, education, projects, skills, links, summaries, and list sections.
- Autosave, version conflict handling, named checkpoints, restore, and a version drawer.
- Live PDF preview rendered with pdf.js, page count, zoom, and download.
- AI drawer for tailoring and scoped edits, with per-operation review and apply. Real LaTeX fix-compile in code mode.
- LaTeX editor with compile preview, save, history, and AI fix.
- Import from a PDF, LaTeX, pasted text, or rough notes, with an editable preview before saving.
- Share links with passwords, expiry, contact visibility, public listing, and per-link view counts.
- Public profile and resume pages, including password locks and a PDF download.
- Link analytics: totals versus the previous period, daily chart, top links, sources, countries, devices,
  and recent opens.
- Master profile editor with autosave and a live sheet.
- Signed-in ATS report with every check and fix, plus job coverage against a parsed posting.
- Staff-only control room: overview, users and account actions, AI spend, revenue, content, and system health.

Next: the production deployment pass (environment, Dodo live mode, and CORS/cookie setup).

## Production notes

- Set `FRONTEND_URL` on the API to the deployed origin; share links and verification/reset email links are built from it.
- Set `VITE_API_URL` for the frontend build, and add the frontend origin to `CORS_ALLOWED_ORIGINS`
  and `CSRF_TRUSTED_ORIGINS` on the API.
- Public share pages live at `/:username` and `/:username/:slug`.
