# Deploying to Vercel (free tier)

The API and the web app deploy as **two separate Vercel projects** from their own repos. The
browser only ever talks to the web app; its server-side proxy calls this API, so CORS isn't needed.

```
Browser ─► careerlift-web.vercel.app (Next.js) ─► careerlift-api.vercel.app (Django) ─► Postgres
                                                                                    └─► Supabase Storage
```

| Piece          | Free service                     |
| -------------- | -------------------------------- |
| API + web app  | Vercel (Hobby)                   |
| PostgreSQL     | Neon or Supabase (with pgvector) |
| Resume uploads | Supabase Storage (S3 API)        |
| AI             | Google AI Studio (Gemini key)    |

## How the API runs on Vercel

- Vercel detects `manage.py` and serves `config.wsgi.application` as a single Python function.
  There is no build artefact to produce; Vercel installs `requirements.txt` on every deploy.
- Python version comes from `.python-version` (3.12).
- `vercel.json` sets a 60 s function limit and keeps tests and docs out of the bundle.
- The build command (`scripts/vercel_build.py`) runs `migrate` on **production** deploys only.
  Preview deploys skip it so unreviewed migrations never touch the production database.
- The filesystem is read-only, so uploads must go to Supabase Storage. The app refuses to start on
  Vercel without the `SUPABASE_S3_*` variables.
- Request bodies are capped at 4.5 MB by Vercel, so resume uploads are limited to 4 MB.
- No sleeping: functions cold-start in a few seconds, unlike free "always-on" hosts that spin down.

## 1. Database

Create a free Postgres database on **Neon** or **Supabase**, then enable pgvector once in its SQL
editor:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Copy the **pooled** connection string (serverless functions open many short connections):

- Neon: the connection string whose host contains `-pooler`.
- Supabase: *Connect → Transaction pooler* (port `6543`).

Make sure it ends with `?sslmode=require`.

## 2. File storage

In Supabase: *Storage → New bucket* named `user-resumes` (private). Then *Project Settings →
Storage → S3 access keys* for the endpoint, region and an access key pair.

## 3. Deploy the API

1. Push this repo to GitHub.
2. On vercel.com: **Add New → Project**, import the repo. Vercel detects Django; keep the defaults.
3. Add **Environment Variables** (Production; add to Preview too if you use preview deploys):

   | Variable                        | Value                                                      |
   | ------------------------------- | ---------------------------------------------------------- |
   | `SECRET_KEY`                    | A new random string (`python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
   | `DEBUG`                         | `False`                                                    |
   | `DATABASE_URL`                  | Pooled connection string from step 1                       |
   | `DB_POOLED`                     | `True`                                                     |
   | `SUPABASE_S3_ENDPOINT`          | From step 2                                                |
   | `SUPABASE_S3_ACCESS_KEY_ID`     | From step 2                                                |
   | `SUPABASE_S3_SECRET_ACCESS_KEY` | From step 2                                                |
   | `SUPABASE_S3_BUCKET_NAME`       | `user-resumes`                                             |
   | `SUPABASE_S3_REGION`            | From step 2                                                |
   | `AI_PROVIDER`                   | `gemini`                                                   |
   | `AI_MODEL`                      | `gemini-3.5-flash-lite`                                    |
   | `GEMINI_API_KEY`                | Your Google AI Studio key                                  |

   `ALLOWED_HOSTS` is optional: Vercel's own hostnames are added automatically. Set it only for a
   custom domain.
4. **Deploy.** The build log should end with the migrations being applied.
5. Check `https://<your-api>.vercel.app/health/` returns `{"status": "ok", "database": "ok"}`.

## 4. Deploy the web app

1. Import the `resume_ai_frontend` repo as a second Vercel project (Next.js is detected).
2. Add one environment variable:
   `DJANGO_API_URL` = `https://<your-api>.vercel.app/api/v1`
3. Deploy, open the site, register, and upload a resume.

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| Build fails at `migrate` | `DATABASE_URL` wrong, or pgvector not enabled (`type "vector" does not exist`). |
| Function crashes with `ImproperlyConfigured` | Missing `SECRET_KEY` or `SUPABASE_S3_*` variables. |
| `/health/` returns 503 | Database unreachable: check the connection string and `sslmode=require`. |
| 400 `Bad Request` on every API call | Calling the API by a hostname not in `ALLOWED_HOSTS` (custom domains). |
| "The AI service is busy" | Gemini free-tier rate limit; wait a minute. |
| Logs | Vercel project → *Logs*. Raise detail with `LOG_LEVEL=INFO`. |
