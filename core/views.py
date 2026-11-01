import logging

from django.db import connection
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request):
    """Liveness + database check for deploy verification and uptime monitors."""
    try:
        connection.ensure_connection()
    except Exception:
        logger.exception("Health check: database unreachable")
        return Response({"status": "error", "database": "unreachable"}, status=503)
    return Response({"status": "ok", "database": "ok"})
