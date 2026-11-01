import os
import urllib.parse
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Vercel sets VERCEL=1 in builds and functions.
ON_VERCEL = bool(os.getenv("VERCEL"))

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"
if not SECRET_KEY and not DEBUG:
    raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG is off.")

ALLOWED_HOSTS = [v.strip() for v in os.getenv("ALLOWED_HOSTS", "").split(",") if v.strip()]
# Vercel's system env vars hold this deployment's hostnames (no scheme).
for _var in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
    if os.getenv(_var):
        ALLOWED_HOSTS.append(os.environ[_var])

if not DEBUG:
    # Vercel terminates TLS and forwards the original scheme in this header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "pgvector.django",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    # Project apps
    "users",
    "resumes",
    "ats",
    "core",
    "billing",
    "jobs",
    "generated_documents",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # must be first
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

def _database_from_url(url: str) -> dict:
    """Parse a postgres:// URL (as set by Vercel's Neon/Supabase integrations)."""
    parsed = urllib.parse.urlparse(url)
    options = dict(urllib.parse.parse_qsl(parsed.query))
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/"),
        "USER": urllib.parse.unquote(parsed.username or ""),
        "PASSWORD": urllib.parse.unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": parsed.port or "",
        "OPTIONS": options,  # e.g. sslmode=require
    }


if os.getenv("DATABASE_URL"):
    DATABASES = {"default": _database_from_url(os.environ["DATABASE_URL"])}
else:
    DATABASES = {
        "default": {
            "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
            "NAME": os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
            "USER": os.getenv("DB_USER", ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", ""),
            "PORT": os.getenv("DB_PORT", ""),
        }
    }
    if os.getenv("DB_SSLMODE"):
        DATABASES["default"]["OPTIONS"] = {"sslmode": os.environ["DB_SSLMODE"]}

# Serverless functions each open their own connection, so production should
# point at a transaction-mode pooler (Neon "-pooler" host, Supabase port 6543).
# Server-side cursors don't survive transaction pooling.
if os.getenv("DB_POOLED", "False") == "True":
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True


# Auth

AUTH_USER_MODEL = "users.Users"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "config.exceptions.custom_exception_handler",
    "UNAUTHENTICATED_USER": None,
}

# JWT

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,  # handled by Users.record_login
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS
CORS_ALLOWED_ORIGINS = [v.strip() for v in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if v.strip()]
CORS_ALLOW_CREDENTIALS = True

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

# File uploads
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
MAX_UPLOAD_SIZE = 4 * 1024 * 1024  # 4MB: Vercel functions reject request bodies over 4.5MB

# Supabase S3 Storage
SUPABASE_S3_ENDPOINT = os.getenv("SUPABASE_S3_ENDPOINT")
SUPABASE_S3_ACCESS_KEY_ID = os.getenv("SUPABASE_S3_ACCESS_KEY_ID")
SUPABASE_S3_SECRET_ACCESS_KEY = os.getenv("SUPABASE_S3_SECRET_ACCESS_KEY")
SUPABASE_S3_BUCKET_NAME = os.getenv("SUPABASE_S3_BUCKET_NAME", "user-resumes")
SUPABASE_S3_REGION = os.getenv("SUPABASE_S3_REGION", "ap-south-1")

if SUPABASE_S3_ENDPOINT and SUPABASE_S3_ACCESS_KEY_ID:
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    AWS_S3_ENDPOINT_URL = SUPABASE_S3_ENDPOINT
    AWS_ACCESS_KEY_ID = SUPABASE_S3_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = SUPABASE_S3_SECRET_ACCESS_KEY
    AWS_STORAGE_BUCKET_NAME = SUPABASE_S3_BUCKET_NAME
    AWS_S3_REGION_NAME = SUPABASE_S3_REGION
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = True  # signed URLs for private bucket
    AWS_S3_SIGNATURE_VERSION = "s3v4"
elif ON_VERCEL:
    # Vercel's filesystem is read-only, so uploads can't fall back to media/.
    raise ImproperlyConfigured("Set the SUPABASE_S3_* variables: uploads need object storage on Vercel.")


AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
# Empty means "use the selected provider's default model" (see core/ai/*_provider.py).
AI_MODEL = os.getenv("AI_MODEL", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Logs go to stdout/stderr, which is what Vercel (and runserver) capture.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "WARNING")},
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
