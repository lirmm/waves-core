from __future__ import unicode_literals

from rest_framework import permissions


class ServiceAccessPermission(permissions.BasePermission):
    message = "Access to service is not allowed"

    def has_object_permission(self, request, view, obj):
        if request.method == 'POST':
            return obj.available_for_user(request.user) and request.user.is_authenticated
        return obj.available_for_user(request.user)

    def has_permission(self, request, view):
        return super(ServiceAccessPermission, self).has_permission(request, view)

