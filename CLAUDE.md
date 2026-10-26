@AGENTS.md

# Rezumiq

Resume builder and AI tailoring. `server/` holds the Django API: Django ORM on Postgres, django-allauth for
email/password and Google sign in plus dev guest accounts, the Tectonic LaTeX compiler, Cloudflare R2 storage and
Dodo Payments. `frontend/` is the React + Vite + TypeScript + Tailwind app, built on Vercel, talking to the API with
session cookies.

## Conventions

- Small, atomic commits, one step at a time. Never add a Co-Authored-By line.
- Never use em dashes, in code, copy, docs or commit messages.
- Boring Python: Django ORM for data (raw SQL only for Postgres features the ORM cannot express, e.g. advisory
  locks), django-allauth for identity, plain Django views with pydantic models for request and response shapes.
- Python style: ruff for lint and format, pytest for tests. Run `ruff check` and `pytest` in `server/` before
  committing backend changes.
- Frontend style: TypeScript strict, pnpm, React Router and TanStack Query. Run `pnpm typecheck` and `pnpm build` in
  `frontend/` before committing frontend changes.
- Comments only where the code can't say it.
- Credentials go in `.env.example` with a comment on where to get them. Never commit a real key.
- Database changes: edit Django models, run `python manage.py makemigrations`, and commit the migration with the
  model change.
