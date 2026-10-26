# Contributing to Rezumiq

Thanks for helping. Rezumiq is an AI resume builder: a Django API in `server/` and a React + Vite app in `frontend/`.

## Ways to help

- **Fix a bug.** Add a test that fails without the fix, then make it pass.
- **Improve the LaTeX templates.** The 14 templates live in `server/templates/`.
- **Improve the frontend.** Screens live in `frontend/src/pages/` and shared pieces in `frontend/src/components/`.
- **Improve the docs.** Setup steps and operational notes are in the two READMEs.

For anything bigger than a bug fix, open an issue first and describe the change.

## Set up

Follow [server/README.md](server/README.md) and [frontend/README.md](frontend/README.md). You need Python 3.13, a
Postgres database (local Docker or a NeonDB branch), and [Tectonic](https://tectonic-typesetting.github.io) for
compile tests. You do not need an AI key: AI features return a clear error and everything else works.

## Make a change

1. Fork (or branch from `main`) and keep each commit to one change.
2. Add a test for any logic you change, one that fails without your fix, in `server/tests/`.
3. Run the same checks CI runs:

   ```sh
   cd server && ruff check . && ruff format --check . && pytest
   cd frontend && pnpm install --frozen-lockfile && pnpm typecheck && pnpm build
   ```

4. Open a pull request that says what changed, why, and how you checked it.

## Conventions

The full rules are in [CLAUDE.md](CLAUDE.md) and [AGENTS.md](AGENTS.md). Keep reuse before adding, prefer stdlib and
Django standard parts, and never commit a key.

## Security

Please don't report security problems in a public issue. Email the address on the maintainer's GitHub profile with
the details and steps to reproduce.

## License

By contributing, you agree that your contribution is licensed under the [MIT License](LICENSE), the same as the rest
of the project.
