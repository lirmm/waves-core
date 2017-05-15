""" Job Runners related models """
from __future__ import unicode_literals

from itertools import chain

from django.db import models
from django.utils.module_loading import import_string

from waves.models.adaptors import HasAdaptorClazzMixin
from waves.models.base import Described, ExportAbleMixin

__all__ = ['Runner']


class RunnerManager(models.Manager):

    def create_default(self, **kwargs):

        return super(RunnerManager, self).create(**kwargs)


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
    # TODO add choices issued from get_importers
    importer_clazz = models.CharField('Importer', max_length=200, null=True, blank=True, choices=[])

    @property
    def importer(self):
        """
        Return an Service AdaptorImporter instance, using either
        :return: an Importer new instance
        """
        # TODO recheck importer
        if self.importer_clazz:
            importer = import_string(self.importer_clazz)
            return importer(self)
        else:
            raise None

    def __str__(self):
        return self.name

    @property
    def serializer(self):
        """ Retrieve a serializer for json export """
        from waves.models.serializers.runners import RunnerSerializer
        return RunnerSerializer

    @property
    def runs(self):
        services_list = self.waves_service_runs.all()
        submissions_list = self.waves_submission_runs.all()
        runs_list = list(chain(services_list, submissions_list))
        return runs_list
