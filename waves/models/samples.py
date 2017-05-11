from __future__ import unicode_literals

from django.db import models
from os.path import basename
from waves.utils.storage import file_sample_directory, waves_storage

__all__ = ['FileInputSample', 'SampleDepParam']


class FileInputSample(models.Model):
    """ Any file input can provide samples """

    class Meta:
        verbose_name_plural = "Input samples"
        verbose_name = "Input sample"

    class_label = "File Input Sample"
    label = models.CharField('Input Label', blank=False, null=True, max_length=255)
    help_text = models.CharField('Help text', blank=True, null=True, max_length=255)
    file = models.FileField('Sample file', upload_to=file_sample_directory, storage=waves_storage, blank=False,
                            null=False)
    file_input = models.ForeignKey('FileInput', on_delete=models.CASCADE, related_name='input_samples')
    dependent_params = models.ManyToManyField('AParam', blank=True, through='SampleDepParam')

    def __str__(self):
        return '%s (%s)' % (self.label, self.name)

    def save_base(self, *args, **kwargs):
        super(FileInputSample, self).save_base(*args, **kwargs)

    @property
    def name(self):
        if self.file:
            return basename(self.file.name)
        else:
            return '--'

    @property
    def required(self):
        return False

    @property
    def default(self):
        return ""



class SampleDepParam(models.Model):
    """ When a file sample is selected, some params may be set accordingly. This class represent this behaviour"""

    class Meta:
        db_table = 'waves_sample_dependent_input'
        verbose_name_plural = "Sample dependencies"
        verbose_name = "Sample dependency"

    # submission = models.ForeignKey('Submission', on_delete=models.CASCADE, related_name='sample_dependent_params')
    file_input = models.ForeignKey('FileInput', null=True, on_delete=models.CASCADE, related_name="sample_dependencies")
    sample = models.ForeignKey(FileInputSample, on_delete=models.CASCADE, related_name='dependent_inputs')
    related_to = models.ForeignKey('AParam', on_delete=models.CASCADE, related_name='related_samples')
    set_default = models.CharField('Set value to ', max_length=200, null=False, blank=False)

    """
    def clean(self):
        if (isinstance(self.related_to, BooleanParam) or isinstance(self.related_to, ListParam)) \
                and self.set_default not in self.related_to.values:
            raise ValidationError({'set_default': 'This value is not possible for related input [%s]' % ', '.join(
                self.related_to.values)})
    """

    def __str__(self):
        return "%s > %s=%s" % (self.sample.label, self.related_to.name, self.set_default)