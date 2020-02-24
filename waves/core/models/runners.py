""" Job Runners related models """

from itertools import chain

from django.db import models
from django.urls import reverse

from waves.core.models.adaptors import HasAdaptorClazzMixin
from waves.core.models.base import Described, ExportAbleMixin

__all__ = ['Runner']


class Runner(Described, ExportAbleMixin, HasAdaptorClazzMixin):
    """ Represents a generic job adapter meta information (resolved at runtime via clazz attribute) """

    class Meta:
        ordering = ['name']
        verbose_name = 'Computing infrastructure'
        verbose_name_plural = "Computing infrastructures"
        db_table = 'wcore_runner'

    name = models.CharField('Label', max_length=50, null=False, help_text='Displayed name')
    enabled = models.BooleanField('Enabled', default=True, null=False, blank=True,
                                  help_text="Runner is enable for job runs")

    @property
    def importer(self):
        """
        Return an Service adapterImporter instance, using either

        :return: an Importer new instance
        """
        if self.adaptor is not None:
            importer = self.adaptor.importer
            importer._runner = self
            return importer
        else:
            return None

    def __str__(self):
        return self.name

    @property
    def serializer(self, context=None):
        """ Retrieve a serializer for json export """
        from import_export.runners import RunnerSerializer
        return RunnerSerializer

    def runs(self):
        services_list = self.running_services().all()
        submissions_list = self.running_submissions().all()
        runs_list = list(chain(services_list, submissions_list))
        return runs_list

    def running_services(self):
        from waves.core.models.services import Service
        return Service.objects.filter(runner=self)

    def running_submissions(self):
        from waves.core.models.services import Submission
        return Submission.objects.filter(runner=self)

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=[self.pk])
