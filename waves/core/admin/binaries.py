from os.path import isfile

from django.contrib.admin import register

from waves.core.admin.base import WavesModelAdmin
from waves.core.models.binaries import ServiceBinaryFile


@register(ServiceBinaryFile)
class ServiceBinaryFileAdmin(WavesModelAdmin):
    model = ServiceBinaryFile
    list_display = ('label', 'created', 'updated', 'file_size', 'file_path')

    def file_size(self, obj):
        if isfile(obj.binary.path):
            return '%s ko' % (obj.binary.size / 1024)
        return "N/A"

    def file_path(self, obj):
        if isfile(obj.binary.path):
            return obj.binary.path
        return "N/A"

    def get_model_perms(self, request):
        # Disable direct entry to BinaryFiles
        return {}
