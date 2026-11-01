"""
Vercel build step (runs after dependencies are installed).

Applies migrations on production deployments only. Preview deployments (every
branch push) share the same database settings, so migrating there would apply
unreviewed migrations to the production database.
"""

import os
import sys

import django
from django.core.management import call_command


def main() -> None:
    env = os.getenv("VERCEL_ENV", "development")
    if env != "production":
        print(f"VERCEL_ENV={env}: skipping migrations (production deployments only).")
        return

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()
    call_command("migrate", interactive=False)


if __name__ == "__main__":
    main()
