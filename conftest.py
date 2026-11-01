"""
Pytest configuration for the CareerLift test suite.

Overrides django_db_setup to enable the pgvector extension on the test
database before Django runs migrations (the `vector` type must exist before
any table with a VectorField can be created).
"""

import pytest
from django.db.backends.base.creation import BaseDatabaseCreation


def _create_test_db_with_vector(self, verbosity=1, autoclobber=False, serialize=True, keepdb=False):
    """
    Drop-in replacement for BaseDatabaseCreation.create_test_db that injects
    CREATE EXTENSION vector between database creation and migration execution.
    """
    from django.core.management import call_command

    test_db_name = self._get_test_db_name()
    self._create_test_db(verbosity=verbosity, autoclobber=autoclobber, keepdb=keepdb)

    old_name = self.connection.settings_dict["NAME"]
    self.connection.settings_dict["NAME"] = test_db_name

    try:
        self.connection.ensure_connection()
        with self.connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        self.connection.connection.commit()
        self.connection.close()

        call_command(
            "migrate",
            "--run-syncdb",
            verbosity=0,
            interactive=False,
            database=self.connection.alias,
        )
    except Exception:
        self.connection.settings_dict["NAME"] = old_name
        raise

    return test_db_name


@pytest.fixture(scope="session")
def django_db_setup(
    django_test_environment,
    django_db_blocker,
    django_db_use_migrations,
    django_db_keepdb,
    django_db_createdb,
    django_db_modify_db_settings,
):
    from django.test.utils import setup_databases, teardown_databases

    _real = BaseDatabaseCreation.create_test_db
    BaseDatabaseCreation.create_test_db = _create_test_db_with_vector

    try:
        with django_db_blocker.unblock():
            db_cfg = setup_databases(verbosity=0, interactive=False)
    finally:
        BaseDatabaseCreation.create_test_db = _real

    yield

    with django_db_blocker.unblock():
        teardown_databases(db_cfg, verbosity=0)
