from django.db import models

from waves.core.utils.storage import binary_storage, binary_directory
from waves.core.models.base import Slugged, TimeStamped


class ServiceBinaryFile(Slugged, TimeStamped):
    class Meta:
        verbose_name = 'Binary file'
        verbose_name_plural = 'Binaries files'
        db_table = 'wcore_servicebinaryfile'

    label = models.CharField('Binary file label', max_length=255, null=False)
    binary = models.FileField('Binary file', upload_to=binary_directory, storage=binary_storage)

    def __str__(self):
        return self.label

    def __unicode__(self):
        return self.label
