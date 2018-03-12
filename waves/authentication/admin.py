from __future__ import unicode_literals

from django.contrib import admin

from waves.authentication.models import WavesApiUser


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created')
    fields = ('user', 'key', 'ip_list', 'domain')
    ordering = ('-created',)


admin.site.register(WavesApiUser, ApiKeyAdmin)
