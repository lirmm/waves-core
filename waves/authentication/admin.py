from __future__ import unicode_literals

from django.contrib import admin

from waves.authentication.models import ApiKey


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'created')
    fields = ('user',)
    ordering = ('-created',)


admin.site.register(ApiKey, ApiKeyAdmin)
