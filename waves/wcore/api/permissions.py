from __future__ import unicode_literals

from rest_framework import permissions


class ServiceAccessPermission(permissions.BasePermission):
    message = "Access to service is not allowed"

    def has_object_permission(self, request, view, obj):
        return obj.available_for_user(request.user)
