""" Adaptors related models super classes """
from __future__ import unicode_literals

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import models
from django.utils.module_loading import import_string

from waves.utils.encrypt import Encrypt
import logging

logger = logging.getLogger(__name__)
__all__ = ['AdaptorInitParam', 'HasRunnerParamsMixin', 'HasAdaptorClazzMixin']


class AdaptorInitParam(models.Model):
    """ Base Class For adaptor initialization params """

    class Meta:
        ordering = ['name']
        verbose_name = "Initial param"
        verbose_name_plural = "Init params"

    _value = None
    _override = None
    name = models.CharField('Name', max_length=100, blank=True, null=True, help_text='Param name')
    value = models.CharField('Value', max_length=500, null=True, blank=True, help_text='Default value')
    crypt = models.BooleanField('Encrypted', default=False, editable=False)
    prevent_override = models.BooleanField('Prevent override', default=False, help_text="Prevent override")

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey(for_concrete_model=False)

    def __str__(self):
        if self.crypt:
            return "%s|********|%s" % (self.name, self.prevent_override)
        return "%s|%s|%s" % (self.name, self.value, self.prevent_override)

    def __init__(self, *args, **kwargs):
        super(AdaptorInitParam, self).__init__(*args, **kwargs)
        self._value = None
        self._override = None

    @classmethod
    def from_db(cls, db, field_names, values):
        """ Decrypt encoded value if needed for params """
        instance = super(AdaptorInitParam, cls).from_db(db, field_names, values)
        if instance.crypt and instance.value:
            instance.value = Encrypt.decrypt(instance.value)
        instance._value = instance.value
        instance._override = instance.prevent_override
        return instance

    def save(self, *args, **kwargs):
        super(AdaptorInitParam, self).save(*args, **kwargs)

    @property
    def config_changed(self):
        return self._value != self.value or self._override != self.prevent_override


class HasAdaptorClazzMixin(models.Model):
    """
    AdaptorClazzMixin models class has a associated concrete adaptor class element,
    where setup params wan be set in AdaptorInitParams models instance.
    """
    class Meta:
        abstract = True

    _adaptor = None
    _clazz = None
    clazz = models.CharField('Adaptor object', max_length=100, null=False,
                             help_text="This is the concrete class used to perform job execution")
    adaptor_params = GenericRelation(AdaptorInitParam)

    def set_run_params_defaults(self):
        """Set runs params with defaults issued from concrete class object """
        object_ctype = ContentType.objects.get_for_model(self)
        # Delete keyx not present in new configuration
        self.adaptor_params.exclude(name__in=self.adaptor.init_params.keys()).delete()
        # keep old values set for runner if key is the same
        adaptors_defaults = self.adaptor.init_params
        current_defaults = self.run_params
        [adaptors_defaults.pop(k, None) for k in current_defaults]
        for name, default in adaptors_defaults.items():
            if name.startswith('crypt_'):
                defaults = {'name': name[6:], 'crypt': True}
            else:
                defaults = {'name': name, 'crypt': False}
            if type(default) in (tuple, list, dict):
                default = default[0][0]
                defaults['prevent_override'] = True
            defaults['value'] = default
            AdaptorInitParam.objects.update_or_create(defaults=defaults, content_type=object_ctype,
                                                      object_id=self.pk, name=name)

    @property
    def run_params(self):
        """ Get defined params values from db """
        return {init.name if init.crypt is False else 'crypt_%s' % init.name: init.value for init in
                self.adaptor_params.all()}

    @property
    def adaptor_defaults(self):
        """ Retrieve init params defined associated concrete class (from clazz attribute) """
        return self.adaptor.init_params

    def __init__(self, *args, **kwargs):
        super(HasAdaptorClazzMixin, self).__init__(*args, **kwargs)

    @classmethod
    def from_db(cls, db, field_names, values):
        """ Executed each time a Service is restored from DB layer"""
        instance = super(HasAdaptorClazzMixin, cls).from_db(db, field_names, values)
        instance._clazz = instance.clazz
        return instance

    @property
    def config_changed(self):
        """ Set whether config has changed before saving """
        return self._clazz != self.clazz # or any([x.has_changed for x in self.adaptor_params.all()])

    @property
    def adaptor(self):
        """ Get and returned an initialized concrete adaptor class parametrized with params defined in db
        :return: a subclass JobAdaptor object instance
        :rtype: JobAdaptor
        """
        if self.clazz is not '' and (self._adaptor is None or self.config_changed):
            self._adaptor = import_string(self.clazz)(**self.run_params)
        return self._adaptor

    @adaptor.setter
    def adaptor(self, adaptor):
        """ Allow to temporarily override current adaptor instance """
        self._adaptor = adaptor


class HasRunnerParamsMixin(HasAdaptorClazzMixin):
    """ Model mixin to manage params overriding and shortcut method to retrieve concrete classes """

    class Meta:
        abstract = True

    _runner = None
    runner = models.ForeignKey('Runner', related_name='%(app_label)s_%(class)s_runs', null=True, blank=False,
                               on_delete=models.SET_NULL,
                               help_text='Service job runs adapter')

    @classmethod
    def from_db(cls, db, field_names, values):
        """ Executed each time a Service is restored from DB layer"""
        instance = super(HasRunnerParamsMixin, cls).from_db(db, field_names, values)
        instance._runner = instance.runner
        return instance

    def set_run_params_defaults(self):
        """ Set runs params with defaults issued from concrete class object """
        if self.runner:
            if self.adaptor_params.count() > 0:
                self.adaptor_params.all().delete()
            runners_defaults = self.runner.run_params
            current_defaults = self.run_params
            [runners_defaults.pop(k, None) for k in current_defaults]
            queryset = self.runner.adaptor_params.filter(
                name__in=runners_defaults.keys()) if runners_defaults else self.runner.adaptor_params.all()
            for runner_param in queryset:
                if runner_param.prevent_override:
                    try:
                        self.adaptor_params.get(name=runner_param.name).delete()
                    except ObjectDoesNotExist:
                        continue
                    except MultipleObjectsReturned:
                        self.adaptor_params.filter(name=runner_param.name).delete()
                else:
                    defaults = {'value': runner_param.value, 'prevent_override': runner_param.prevent_override,
                                'crypt': runner_param.crypt}
                    object_ctype = ContentType.objects.get_for_model(self)
                    obj, created = AdaptorInitParam.objects.update_or_create(defaults=defaults,
                                                                             content_type=object_ctype,
                                                                             object_id=self.pk, name=runner_param.name)
                    logger.debug('Object %s, %s', obj, created)

    @property
    def clazz(self):
        return self.get_runner().clazz if self.get_runner() else None

    @property
    def config_changed(self):
        return self._runner != self.runner

    @property
    def run_params(self):
        """
        Return a list of tuples representing current service adaptor init params
        :return: a Dictionary (param_name=param_service_value or runner_param_default if not set
        :rtype: dict
        """
        object_params = super(HasRunnerParamsMixin, self).run_params
        runners_default = self.get_runner().run_params
        runners_default.update(object_params)
        return runners_default

    @property
    def adaptor_defaults(self):
        """ Retrieve init params defined associated concrete class (from runner attribute) """
        return self.get_runner().run_params if self.get_runner() else {}

    def get_runner(self):
        """ Return effective runner (could be overridden is any subclasses) """
        return self.runner
