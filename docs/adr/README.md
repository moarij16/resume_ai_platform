# Architecture Decision Records

Each significant decision (architecture, data model, cost, or anything hard to reverse) gets a
short record here. Records are numbered and never rewritten. To change a decision, write a new ADR
that supersedes the old one, then update the old one's status.

To add one, copy [`template.md`](template.md) to `NNNN-short-title.md` with the next number.

| ADR                                     | Title                                                 | Status   |
| --------------------------------------- | ----------------------------------------------------- | -------- |
| [0001](0001-layered-django-apps.md)     | Use thin ViewSets, serializer validation, fat models  | Accepted |
| [0002](0002-local-jwt-authentication.md) | Use local email/password auth with rotating JWTs      | Accepted |
