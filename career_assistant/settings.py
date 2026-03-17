import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")


# Application definition

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "pgvector.django",
    # Third party
    "rest_framework",
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

ROOT_URLCONF = "career_assistant.urls"

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

WSGI_APPLICATION = "career_assistant.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

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


# Password validation

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "users.authentication.SupabaseAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "career_assistant.exceptions.custom_exception_handler",
    "UNAUTHENTICATED_USER": None,
}
# AWS Cognito

# AWS_COGNITO_REGION = os.getenv("AWS_COGNITO_REGION")
# AWS_COGNITO_USER_POOL_ID = os.getenv("AWS_COGNITO_USER_POOL_ID")
# AWS_COGNITO_APP_CLIENT_ID = os.getenv("AWS_COGNITO_APP_CLIENT_ID")
# AWS_COGNITO_JWKS_URL = (
#     f"https://cognito-idp.{AWS_COGNITO_REGION}.amazonaws.com/"
#     f"{AWS_COGNITO_USER_POOL_ID}/.well-known/jwks.json"
# )

# Supabase Auth

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

# CORS
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
CORS_ALLOW_CREDENTIALS = True

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

# File uploads
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB


AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o")
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

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
