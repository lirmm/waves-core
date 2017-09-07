from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin import register
from waves.wcore.models import ServiceBinaryFile


@register(ServiceBinaryFile)
class ServiceBinaryFileAdmin(admin.ModelAdmin):
    model = ServiceBinaryFile


