from unittest.mock import patch

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_is_public_and_checks_database():
    response = APIClient().get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.django_db
def test_health_reports_unreachable_database():
    with patch("core.views.connection.ensure_connection", side_effect=Exception("down")):
        response = APIClient().get("/health/")
    assert response.status_code == 503
    assert response.json()["database"] == "unreachable"
