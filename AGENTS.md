# CareerLift API: agent guide

Django 4.2 + Django REST Framework API for CareerLift: resume parsing, ATS scoring, job
descriptions and AI document generation. The web client lives in a separate repo
(`resume_ai_frontend`, Next.js), which calls this API through its own server-side proxy.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for branches, commits and PRs, and
[docs/architecture.md](docs/architecture.md) for how the pieces fit together.

## Commands

Run everything from the repo root with the virtualenv active (`venv\Scripts\activate` on Windows).

| Task                 | Command                                                |
| -------------------- | ------------------------------------------------------ |
| Dev server (:8000)   | `python manage.py runserver` (or `start.bat`)          |
| Migrations           | `python manage.py makemigrations` / `migrate`          |
| System check         | `python manage.py check`                               |
| Tests                | `pytest` (needs `pytest` + `pytest-django` installed)  |
| Format               | `black <changed files>`                                |

Tests run against PostgreSQL with the `vector` extension. `conftest.py` creates the extension on
the test database before migrations, so the configured DB user needs permission to do that.

## Architecture rules

Every app follows the same layering. Put logic in the layer that owns it.

| Layer       | File             | Owns                                                              |
| ----------- | ---------------- | ----------------------------------------------------------------- |
| ViewSet     | `views.py`       | HTTP only: permissions, picking the serializer, status codes      |
| Serializer  | `serializers.py` | Validation, transformation, calling model factories in `create()` |
| Model       | `models.py`      | CRUD, domain logic, state transitions, query helpers              |
| Service     | `services/`      | External or heavy work: AI calls, file parsing, scoring           |
| URLs        | `urls.py`        | Router registration only                                          |

- **Thin ViewSets.** No business rules, no ORM work beyond `get_queryset()`, no data shaping.
- **Fat models.** Creation goes through classmethods (e.g. `Resume.create_from_upload()`); state
  changes are model methods, not field assignments in serializers or views.
- **Serializers validate.** Raise `serializers.ValidationError` there. Model methods raise
  `ValueError` or domain exceptions; let `config.exceptions.custom_exception_handler` turn them
  into responses instead of catching them in views.
- **Services stay framework-light.** `scanner/` and `core/ai/` must not depend on DRF request
  objects. AI providers implement `core/ai/base_provider.py`; prompts live in `core/ai/prompts/`.
- Every model extends `core.base.BaseModel` (UUID primary key, timestamps, soft-delete fields).

## Access policy

Users can only see and change their own records. Use the shared pieces rather than hand-written
filters:

- **Models:** user-owned models extend `core.base.UserOwnedModel`. Its default manager hides
  soft-deleted rows (`all_objects` includes them); `Model.owned_by(user)` returns that user's live
  records. Don't add managers to `BaseModel`: `Users` would inherit them and break auth.
- **ViewSets:** add `core.mixins.OwnedResourceMixin` and set `owned_model`. It scopes the queryset
  to `owned_by(request.user)` and applies `IsAuthenticated` + `core.permissions.IsOwner`. Other
  users' records return 404, not 403, so their existence isn't revealed.
- **Request bodies:** reference other records with `core.fields.OwnedResourceIdField(Model,
  "X not found.")`, and pass `context={"request": request}`. Foreign, deleted and missing IDs all
  get the same error.
- Covered by `core/test_access_policy.py`. Add a case there for every new owned resource.

## AI errors

`call_ai` (`generated_documents/services/utils.py`) is the only entry point. Failures become 503s
with fixed, user-facing messages: `AIProviderNotConfigured` (unknown provider or missing key),
`AIRateLimited` (provider 429) and `AIGenerationFailed`. The provider's own error text is logged
with `logger.exception` and never returned.

## API contract

The frontend's TypeScript types (`src/types/api.ts` in `resume_ai_frontend`) mirror these
serializers. When you change a serializer field, an endpoint or a JSON shape (`resume_data`,
`scan_result`, `document_content`), update the frontend types in the same change, or note it in the
PR so it can be.

- Routes live under `/api/v1/<app>/` and always end with a trailing slash.
- Errors go through `config/exceptions.py` as `{ error, status_code, detail }`. New endpoints
  should raise exceptions rather than build ad-hoc error dicts.
- Lists are unpaginated JSON arrays.
- Auth: simplejwt Bearer tokens. Refresh tokens rotate and are blacklisted after use.

## Known issues

Check these before you rely on the behaviour, and fix them deliberately in their own PR:

- `ats_service` reads `resume_length` but the analyzer returns `resume_length_score`, so
  `breakdown.resume_length` is always `null`.
- `POST /api/v1/resumes/` (router create) has no writable fields and errors. Use `/upload/`.
- `users/permissions.py` refers to `is_admin`, `is_premium` and `is_within_limits`, which the user
  model doesn't have.
- `resumes/tests.py::test_upload_response_shape` is stale: it expects the pre-`0ff1836` upload
  response (top-level `id`), but the endpoint returns `{resume, ats_scan}`.
- The ATS scan and resume upload views still catch broad exceptions and return `str(e)` as a 400.
- Media files aren't served in local development (`original_file_url` is a relative path).
- The codebase isn't fully `black`-formatted yet. Format only the files you touch.

## Don'ts

- Don't commit `.env`, `media/`, `venv/` or `__pycache__/`.
- Don't edit an applied migration. Add a new one.
- Don't call AI providers from views or serializers. Go through `core/ai/service.py`.
- Don't log or return secrets, tokens or raw provider errors to clients.
