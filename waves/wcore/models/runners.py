""" Job Runners related models """
from __future__ import unicode_literals

from itertools import chain

from django.contrib.contenttypes.models import ContentType
from django.db import models

from waves.wcore.models import AdaptorInitParam
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
        verbose_name = 'Execution environment'
        verbose_name_plural = "Executions environments"
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
    def serializer(self, context=None):
        """ Retrieve a serializer for json export """
        from waves.wcore.models.serializers.runners import RunnerSerializer
        return RunnerSerializer

    @property
    def runs(self):
        services_list = self.running_services.all()
        submissions_list = self.running_submissions.all()
        runs_list = list(chain(services_list, submissions_list))
        return runs_list

    @property
    def running_services(self):
        from waves.wcore.models import get_service_model
        Service = get_service_model()
        return Service.objects.filter(runner=self)

    @property
    def running_submissions(self):
        from waves.wcore.models import get_submission_model
        Submission = get_submission_model()
        return Submission.objects.filter(runner=self)


class HasRunnerParamsMixin(HasAdaptorClazzMixin):
    """ Model mixin to manage params overriding and shortcut method to retrieve concrete classes """

    class Meta:
        abstract = True

    _runner = None
    runner = models.ForeignKey(Runner, related_name='%(app_label)s_%(class)s_runs', null=True, blank=False,
                               on_delete=models.SET_NULL,
                               help_text='Service job runs adapter')

    @classmethod
    def from_db(cls, db, field_names, values):
        """ Executed each time a Service is restored from DB layer"""
        instance = super(HasRunnerParamsMixin, cls).from_db(db, field_names, values)
        instance._runner = instance.runner
        return instance

    @property
    def clazz(self):
        """ Return associated runner clazz setup """
        return self.get_runner().clazz if self.get_runner() else None

    @clazz.setter
    def clazz(self):
        # Do nothing when setting clazz attribute, not set in DB
        pass

    @property
    def config_changed(self):
        return self._runner != self.get_runner() or self._clazz != self.clazz

    @property
    def run_params(self):
        """
        Return a list of tuples representing current service adaptor init params
        :return: a Dictionary (param_name=param_service_value or runner_param_default if not set
        :rtype: dict
        """
        # Retrieve the ones defined in DB
        object_params = super(HasRunnerParamsMixin, self).run_params
        # Retrieve the ones defined for runner
        runners_params = self.get_runner().run_params
        # Merge them
        runners_params.update(object_params)
        return runners_params

    @property
    def adaptor_defaults(self):
        """ Retrieve init params defined associated concrete class (from runner attribute) """
        return self.get_runner().run_params if self.get_runner() else {}

    def get_runner(self):
        """ Return effective runner (could be overridden is any subclasses) """
        return self.runner

    def set_defaults(self):
        """Set runs params with defaults issued from adaptor class object """
        # Reset all old values
        self.adaptor_params.all().delete()
        object_ctype = ContentType.objects.get_for_model(self)
        for runner_param in self.get_runner().adaptor_params.filter(prevent_override=False):
            AdaptorInitParam.objects.create(name=runner_param.name,
                                            value=runner_param.value,
                                            crypt=(runner_param.name == 'password'),
                                            prevent_override=False,
                                            content_type=object_ctype,
                                            object_id=self.pk)
