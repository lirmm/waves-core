from django.contrib import admin

from waves.authentication.models import WavesApiUser


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created')
    fields = ('user', 'created', 'key', 'ip_list', 'domain')
    ordering = ('-created',)
    readonly_fields = ('user', 'created', 'key')


admin.site.register(WavesApiUser, ApiKeyAdmin)
