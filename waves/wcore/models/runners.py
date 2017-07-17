""" Job Runners related models """
from __future__ import unicode_literals

from itertools import chain

from django.db import models
from django.utils.module_loading import import_string

from waves.wcore.models.adaptors import HasAdaptorClazzMixin
from waves.wcore.models.base import Described, ExportAbleMixin

__all__ = ['Runner']


class RunnerManager(models.Manager):

    def create_default(self, **kwargs):
        return super(RunnerManager, self).create(**kwargs)

    def create(self, *args, **kwargs):
        return super(RunnerManager, self).create(*args, **kwargs)


class Runner(Described, ExportAbleMixin, HasAdaptorClazzMixin):
    """ Represents a generic job adaptor meta information (resolved at runtime via clazz attribute) """
    # TODO manage cleanly change in actual clazz value (when changed)

    class Meta:
        ordering = ['name']
        db_table = 'waves_runner'
        verbose_name = 'Execution'
        verbose_name_plural = "Execution"
    objects = RunnerManager()
    name = models.CharField('Label', max_length=50, null=False, help_text='Displayed name')
    enabled = models.BooleanField('Enabled', default=True, null=False, blank=True,
                                  help_text="Runner is enable for job runs")

    @property
    def importer(self):
        """
        Return an Service AdaptorImporter instance, using either
        :return: an Importer new instance
        """
        # TODO recheck importer
        if self.adaptor is not None:
            return self.adaptor.importer
        else:
            return None

    def __str__(self):
        return self.name

    @property
    def serializer(self):
        """ Retrieve a serializer for json export """
        from waves.wcore.models.serializers.runners import RunnerSerializer
        return RunnerSerializer

    @property
    def runs(self):
        services_list = self.wcore_service_runs.all()
        submissions_list = self.wcore_submission_runs.all()
        runs_list = list(chain(services_list, submissions_list))
        return runs_list
