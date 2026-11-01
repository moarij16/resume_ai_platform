# Architecture

CareerLift helps job seekers get past applicant tracking systems (ATS). Users upload a resume, see
how an ATS would score it, match it against job descriptions, and generate tailored documents
with AI.

## System overview

```
Browser ──► Next.js frontend (resume_ai_frontend)
              │  BFF route handlers keep the JWTs in httpOnly cookies
              ▼
            Django REST API (this repo)  /api/v1/*
              ├── PostgreSQL + pgvector
              ├── File storage: local media/ or Supabase S3
              └── AI providers: OpenAI | Anthropic | Gemini
```

The browser never talks to Django directly. The frontend's `/api/proxy/*` route attaches the
access token and refreshes it on a 401, so CORS is only needed if you call the API from another
origin.

## Apps

| App                   | Responsibility                                                    |
| --------------------- | ----------------------------------------------------------------- |
| `users`               | Custom email user, registration, JWT auth, profile                |
| `resumes`             | Upload (PDF/DOCX, up to 5 MB), parsing into `resume_data`, edits  |
| `jobs`                | Saved job descriptions (with a pgvector embedding column)         |
| `ats`                 | ATS scans: `resume_only` and `jd_match` modes, history            |
| `generated_documents` | AI cover letters, LinkedIn bios, resume rewrites; PDF/DOCX export |
| `billing`             | Subscription models (endpoints are stubs)                         |
| `core`                | `BaseModel`, mixins, exception handler, AI provider abstraction   |
| `scanner/`            | Plain-Python parsing and scoring engine (not a Django app)        |

## Request flow

```
urls.py ─► ViewSet (HTTP only)
              └─► Serializer (validate / transform)
                     └─► Model classmethod / method (domain logic, persistence)
                            └─► services/ (AI, parsing, scoring)
```

For example, `POST /resumes/upload/` validates the file in `ResumeUploadSerializer` and creates
the row with `Resume.create_from_upload()`, which parses it through `resumes/services`. It then
runs a `resume_only` scan through `ats/services/ats_service.py`.

## Key data shapes

- `Resume.resume_data` (JSON): `raw_text`, `word_count`, `metadata`, `sections`,
  `detected_skills`, `skills_detail`, `bullets`, `experience`. Every scan and generator reads
  `raw_text`.
- `ATSScan.breakdown` / `scan_result`: the shape depends on `scan_mode` (see
  `scanner/models/resume_analyzer.py` and `scanner/scorers/ats_scorer.py`).
- `GeneratedDocument.document_content`: plain text for cover letters, and a JSON string for
  resumes and LinkedIn bios. If the AI output can't be parsed, the raw text is stored instead.

## AI layer

`core/ai/service.py` selects a provider from `AI_PROVIDER` / `AI_MODEL`. Providers implement
`core/ai/base_provider.py`, and prompt sets live in `core/ai/prompts/`. Generation runs
synchronously inside the request. A provider failure raises `AIGenerationFailed`, which surfaces
as a 503.

## Decisions

See [docs/adr/](adr/README.md).
