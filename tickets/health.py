import time

from django.db import DatabaseError, connection
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

STARTED_AT = time.monotonic()


class HealthSerializer(serializers.Serializer):
    service = serializers.CharField()
    status = serializers.CharField()
    database = serializers.CharField()
    uptime_seconds = serializers.FloatField(min_value=0)


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: HealthSerializer, 503: HealthSerializer},
        auth=[],
    )
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                healthy = cursor.fetchone() == (1,)
        except DatabaseError:
            healthy = False
        return Response(
            {
                "service": "halcyon-ticketing-api",
                "status": "ok" if healthy else "degraded",
                "database": "connected" if healthy else "unavailable",
                "uptime_seconds": round(time.monotonic() - STARTED_AT, 3),
            },
            status=200 if healthy else 503,
        )
