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

Copy `.env.example` to `.env` and fill in the values. Keys that are commented
out are optional — leave them commented rather than blank, since an empty value
overrides the default.

---

## Authentication

Auth is handled locally: Django stores users (email + hashed password) and
issues JWTs via `djangorestframework-simplejwt`.

| Method | Endpoint | Body |
|---|---|---|
| POST | `/api/v1/users/auth/register/` | `email`, `password`, `first_name`, `last_name` |
| POST | `/api/v1/users/auth/login/` | `email`, `password` |
| POST | `/api/v1/users/auth/refresh/` | `refresh` |
| POST | `/api/v1/users/auth/logout/` | `refresh` |
| POST | `/api/v1/users/me/change-password/` | `current_password`, `new_password` |

Register and login return `access` and `refresh` tokens. All other endpoints require:

```
Authorization: Bearer <access_token>
```

Access tokens last 15 minutes and refresh tokens 7 days (`JWT_ACCESS_MINUTES`,
`JWT_REFRESH_DAYS`). Each refresh issues a new refresh token and blacklists the old one.
