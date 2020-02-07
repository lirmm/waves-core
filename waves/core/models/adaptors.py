""" Adaptors models classes """
from __future__ import unicode_literals

import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.module_loading import import_string

from waves.core.adaptors.loader import AdaptorLoader
from waves.core.models.base import WavesBaseModel
from waves.core.models.binaries import ServiceBinaryFile
from waves.core.utils.encrypt import Encrypt

logger = logging.getLogger(__name__)
__all__ = ['AdaptorInitParam', 'HasAdaptorClazzMixin']


class AdaptorInitParam(WavesBaseModel):
    """ Base Class For adapter initialization params """

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
    content_object = GenericForeignKey(for_concrete_model=True)

    def __str__(self):
        if self.crypt:
            return "{}|********|{}".format(self.name, self.prevent_override)
        return "{}|{}|{}".format(self.name, self.value, self.prevent_override)

    def __unicode__(self):
        if self.crypt:
            return "{}|********|{}".format(self.name, self.prevent_override)
        return "{}|{}|{}".format(self.name, self.value, self.prevent_override)

    def __init__(self, *args, **kwargs):
        super(AdaptorInitParam, self).__init__(*args, **kwargs)
        self._value = None
        self._override = None

    @classmethod
    def from_db(cls, db, field_names, values):
        """ Decrypt encoded value if needed for params """
        instance = super(AdaptorInitParam, cls).from_db(db, field_names, values)
        if instance.name == "password" and instance.value:
            instance.value = Encrypt.decrypt(instance.value)
        instance._value = instance.get_value()
        instance._override = instance.prevent_override
        return instance

    def get_value(self):
        if self.name == "command" and self.content_object is not None:
            if self.content_object.binary_file is not None:
                return self.content_object.binary_file.binary.path
        return self.value

    @property
    def config_changed(self):
        return self._value != self.value or self._override != self.prevent_override


class HasAdaptorClazzMixin(WavesBaseModel):
    """
    AdaptorClazzMixin models class has a associated concrete adapter class element,
    where setup params wan be set in AdaptorInitParams models instance.
    """

    class Meta:
        abstract = True

    _adaptor = None
    _clazz = None
    clazz = models.CharField('adapter object', max_length=100, null=False,
                             help_text="This is the concrete class used to perform job execution")
    adaptor_params = GenericRelation(AdaptorInitParam)

    binary_file = models.ForeignKey(ServiceBinaryFile, null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text="If set, 'Execution parameter' param line:'command' will be ignored")

    def set_defaults(self):
        """Set runs params with defaults issued from adapter class object """
        # Reset all old values
        self.adaptor_params.all().delete()
        object_ctype = ContentType.objects.get_for_model(self)
        for name, default in self.adaptor_defaults.items():
            if name == 'password':
                defaults = {'name': name, 'crypt': True}
            else:
                defaults = {'name': name, 'crypt': False}
            if type(default) in (tuple, list, dict):
                default = default[0][0]
                defaults['prevent_override'] = True
            else:
                defaults['prevent_override'] = False
            defaults['value'] = default
            AdaptorInitParam.objects.create(name=defaults['name'],
                                            value=defaults['value'],
                                            prevent_override=defaults['prevent_override'],
                                            content_type=object_ctype,
                                            object_id=self.pk)

    @property
    def run_params(self):
        """ Get defined params values from db

            .. WARNING::

                This method will display raw password non encoded value

        """
        return {init.name: init.get_value() for init in self.adaptor_params.all()}

    def display_params(self):
        """ return string representation for related params """
        return ['%s:%s' % (name, value if name != 'password' else "*****") for name, value in
                self.run_params.items()]

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
        return self._clazz != self.clazz  # or any([x.has_changed for x in self.adaptor_params.all()])

    @property
    def adaptor(self):
        """ Get and returned an initialized concrete adapter class parametrized with params defined in db

        :return: a subclass JobAdaptor object instance
        :rtype: JobAdaptor
        """
        if self.clazz and (self._adaptor is None or self.config_changed):
            try:
                self._adaptor = import_string(self.clazz)(**self.run_params)
            except ImportError as e:
                logger.error('Import Adapter error {}'.format(e))
                self._adaptor = None
        return self._adaptor

    @adaptor.setter
    def adaptor(self, adaptor):
        """ Allow to temporarily override current adapter instance """
        self._adaptor = adaptor

    def save(self, *args, **kwargs):
        super(HasAdaptorClazzMixin, self).save(*args, **kwargs)
        names = AdaptorLoader.get_class_names()
        if self.clazz and self.clazz not in names:
            raise RuntimeError('The class [{}] not configured as ADAPTORS_CLASSES {}'.format(self.clazz, names))
