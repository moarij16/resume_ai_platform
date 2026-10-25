# 0001. Use thin ViewSets, serializer validation and fat models

- **Status:** Accepted
- **Date:** 2026-10-25

## Context

Each app exposes REST endpoints over a few models. Without a convention, business rules end up
spread across views, serializers and helper functions, which makes behaviour hard to find and
test.

## Decision

- **ViewSets** handle HTTP only: permissions, picking the serializer, status codes and
  `get_queryset()` scoped to `request.user`.
- **Serializers** validate input, transform representations and call model factories from
  `create()` / `update()`.
- **Models** own creation classmethods (e.g. `Resume.create_from_upload`), state transitions and
  domain queries.
- **`services/`** modules wrap external or heavy work (AI providers, file parsing, scoring) and
  don't depend on DRF request objects.
- Every model extends `core.base.BaseModel` (UUID primary key, timestamps, soft-delete fields).

## Alternatives considered

- **Logic in views:** quick to write, but hard to reuse and test outside HTTP.
- **Service layer for everything:** more indirection than a project this size needs. Services
  are reserved for integrations.

## Consequences

Domain logic can be tested without HTTP, and views stay uniform. Reviewers must push back when
logic creeps into views. Revisit this if an app grows workflows that span several models.
