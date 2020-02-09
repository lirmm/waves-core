""" Job Runners related models """

from itertools import chain

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse

from waves.core.models import AdaptorInitParam
from waves.core.models.adaptors import HasAdaptorClazzMixin
from waves.core.models.base import Described, ExportAbleMixin

__all__ = ['Runner', 'HasRunnerParamsMixin']


class Runner(Described, ExportAbleMixin, HasAdaptorClazzMixin):
    """ Represents a generic job adapter meta information (resolved at runtime via clazz attribute) """

    class Meta:
        ordering = ['name']
        verbose_name = 'Computing infrastructure'
        verbose_name_plural = "Computing infrastructures"
        app_label = "wcore"

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

    def __unicode__(self):
        return self.name

    @property
    def serializer(self, context=None):
        """ Retrieve a serializer for json export """
        from waves.core.import_export.runners import RunnerSerializer
        return RunnerSerializer

    @property
    def runs(self):
        services_list = self.running_services.all()
        submissions_list = self.running_submissions.all()
        runs_list = list(chain(services_list, submissions_list))
        return runs_list

    @property
    def running_services(self):
        from waves.core.models import Service
        return Service().objects.filter(runner=self)

    @property
    def running_submissions(self):
        from waves.core.models import Submission
        return Submission().objects.filter(runner=self)

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=[self.pk])


class HasRunnerParamsMixin(HasAdaptorClazzMixin):
    """ Model mixin to manage params overriding and shortcut method to retrieve concrete classes """

    class Meta:
        abstract = True

    _runner = None
    runner = models.ForeignKey(Runner, verbose_name="Computing infrastructure",
                               related_name='%(app_label)s_%(class)s_runs',
                               null=True, blank=False, on_delete=models.SET_NULL,
                               help_text='Service job runs configuration')

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
    def clazz(self, value):
        # Do nothing when setting clazz attribute, not set in DB
        pass

    @property
    def config_changed(self):
        return self._runner != self.get_runner() or self._clazz != self.clazz

    @property
    def run_params(self):
        """
        Return a list of tuples representing current service adapter init params

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
        """Set runs params with defaults issued from adapter class object """
        # Reset all old values
        self.adaptor_params.all().delete()
        object_ctype = ContentType.objects.get_for_model(self)
        if self.get_runner() is not None:
            for runner_param in self.get_runner().adaptor_params.filter(prevent_override=False):
                AdaptorInitParam.objects.create(name=runner_param.name,
                                                value=runner_param.value,
                                                crypt=(runner_param.name == 'password'),
                                                prevent_override=False,
                                                content_type=object_ctype,
                                                object_id=self.pk)
