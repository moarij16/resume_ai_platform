# Contributing to the CareerLift API

## Setup

See [README.md](README.md). In short: Python 3.11, a virtualenv, `pip install -r requirements.txt`,
copy `.env.example` to `.env`, then run `python manage.py migrate`. For tests, also run
`pip install pytest pytest-django`.

## Branches

| Branch      | Purpose                                                   |
| ----------- | --------------------------------------------------------- |
| `master`    | Production. Only updated by release PRs from `dev`.       |
| `dev`       | Integration branch and the default PR target.             |
| `feature/*` | New functionality, e.g. `feature/ats-keyword-density`     |
| `fix/*`     | Bug fixes                                                 |
| `chore/*`   | Tooling, dependencies, configuration                      |
| `docs/*`    | Documentation only                                        |

Branch from `dev` and open a PR back into `dev`. Never force-push to `master` or `dev`, and never
rewrite pushed history. Address review comments with new commits on the same branch.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <imperative summary>

feat(ats): add keyword density to JD match results
fix(resumes): keep raw_text when resume_data is patched
docs(adr): record local JWT authentication
```

- **Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`,
  `revert`
- **Scopes** (optional): `users`, `resumes`, `jobs`, `ats`, `documents`, `billing`, `core`, `ai`,
  `scanner`, `config`, `db`, `deps`, `ci`, `docs`, `adr`, `release`
- One concern per commit. Keep the summary line short and put detail in the body. No "wip" or
  "fix stuff" commits.
- Never commit secrets, `.env` (only `.env.example`), `media/` uploads or generated files.

## Pull requests

Use the [PR template](.github/pull_request_template.md). Every PR includes:

1. **Summary:** what changed and why
2. **What changed:** the notable changes and decisions
3. **API changes:** new or changed endpoints and response shapes. The frontend mirrors these in
   `src/types/api.ts`, so list them explicitly.
4. **How to test:** a step-by-step manual checklist
5. **Known limitations**

CI (`python manage.py check`, migration check and tests) must pass. Passing CI doesn't replace
manual testing.

## Releases

A release PR from `dev` into `master` carries a changelog. After it merges, tag the release
(`v0.1.0`, …).

## Code standards

- Follow the layering in [AGENTS.md](AGENTS.md#architecture-rules): thin ViewSets, validation in
  serializers, domain logic in models, external work in `services/`.
- Format touched files with `black`. Prefer type hints on new functions.
- Scope every queryset to `request.user`.
- Every model change ships with its migration. Never edit an applied migration.
- Add or update tests for new behaviour (`<app>/tests.py` or `scanner/tests/`).
- User-facing errors must be friendly. Log provider and stack details server-side only.
- Record significant decisions as an [ADR](docs/adr/). Copy `docs/adr/template.md` to start one.
- Update `.env.example` and the README whenever you add configuration.
