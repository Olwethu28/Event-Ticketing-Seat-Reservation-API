from rest_framework.permissions import SAFE_METHODS, BasePermission

from tickets.models import User


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == User.Role.ADMIN)


class AdminOnly(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user)


class AdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.method in SAFE_METHODS or is_admin(request.user)
        )
