# CareerLift — Backend API

Django REST Framework + Supabase + PostgreSQL

---

## Setup

```bash
# 1. Clone and navigate
git clone https://github.com/your-username/resume-ai-platform.git
cd resume_ai_platform

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
python -m pip install -r requirements.txt

# 4. Create .env file (see .env.example)

# 5. Run migrations
python manage.py migrate

# 6. Start server
python manage.py runserver
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=
DB_HOST=db.your-project.supabase.co
DB_PORT=5432

SUPABASE_URL=
SUPABASE_JWKS_URL=
SUPABASE_SECRET_KEY=

OPENAI_API_KEY=

CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## Authentication

All endpoints require:

```
Authorization: Bearer <supabase_access_token>
```

Get a token via Supabase Auth before making requests.
