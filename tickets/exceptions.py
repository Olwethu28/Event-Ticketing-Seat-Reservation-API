import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with the current resource state."
    default_code = "conflict"


def error_payload(status_code, code, message, details, path):
    return {
        "error": {
            "status": status_code,
            "code": code,
            "message": message,
            "details": details,
            "path": path,
            "timestamp": timezone.now().isoformat(),
        }
    }


def api_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(
            exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        )
    elif isinstance(exc, ProtectedError):
        exc = Conflict("This resource is referenced by other records.")
    elif isinstance(exc, IntegrityError):
        exc = Conflict("A database constraint prevented this change.")
    response = exception_handler(exc, context)
    path = context["request"].path
    if response is None:
        logger.error("Unhandled API exception", exc_info=exc)
        return Response(
            error_payload(500, "server_error", "Internal server error.", None, path),
            status=500,
        )
    details = response.data
    code = getattr(exc, "default_code", "error")
    message = (
        str(details["detail"])
        if isinstance(details, dict) and "detail" in details
        else "Request validation failed."
    )
    response.data = error_payload(response.status_code, code, message, details, path)
    return response


def handler404(request, exception):
    return JsonResponse(
        error_payload(404, "not_found", "Resource not found.", None, request.path),
        status=404,
    )


def handler500(request):
    return JsonResponse(
        error_payload(
            500, "server_error", "Internal server error.", None, request.path
        ),
        status=500,
    )
