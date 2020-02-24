"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the GNU GPL v3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       https://www.gnu.org/licenses/gpl-3.0.en.html
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""



import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.module_loading import import_string

from waves.core.loader import AdaptorLoader
from waves.core.utils import Encrypt

logger = logging.getLogger(__name__)
__all__ = ['AdaptorInitParam', 'HasAdaptorClazzMixin']


class AdaptorInitParam(models.Model):
    """ Base Class For adapter initialization params """

    class Meta:
        ordering = ['name']
        verbose_name = "Initial param"
        verbose_name_plural = "Init params"
        db_table = 'wcore_adaptorinitparam'

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
        instance._value = instance.value
        instance._override = instance.prevent_override
        return instance

    def get_value(self):
        if self.name == "password" and self.value:
            return "x" * len(self.value)
        return self.value

    @property
    def config_changed(self):
        return self._value != self.value or self._override != self.prevent_override


class HasAdaptorClazzMixin(models.Model):
    """
    AdaptorClazzMixin models class has a associated concrete adapter class element,
    where setup params wan be set in AdaptorInitParams models instance.
    """

    class Meta:
        abstract = True

    _adaptor = None
    _clazz = None
    clazz = models.CharField('Adapter object',
                             max_length=100,
                             null=True,
                             help_text="This is the concrete class used to perform job execution")
    adaptor_params = GenericRelation(AdaptorInitParam)

    def set_defaults(self):
        """Set runs params with defaults issued from adapter class object """
        # Reset all old values
        self.adaptor_params.all().delete()
        object_type = ContentType.objects.get_for_model(self)
        for name, default in self.adaptor_defaults.items():
            if name in ('password', 'pass', 'auth', 'passphrase'):
                defaults = {'name': name, 'crypt': True}
            else:
                defaults = {'name': name, 'crypt': False}
            if type(default) in (tuple, list, dict):
                default = default[0][0]
                defaults['prevent_override'] = True
            else:
                defaults['prevent_override'] = False
            defaults['value'] = default
            AdaptorInitParam.objects.update_or_create(name=name,
                                                      content_type=object_type,
                                                      object_id=self.pk,
                                                      defaults={
                                                          'prevent_override': defaults['prevent_override'],
                                                          'value': defaults['value']
                                                      })

    @property
    def run_params(self):
        """ Get defined params values from db """
        return {x.name: x.get_value() for x in self.adaptor_params.all()}

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

    def __repr__(self):
        return super().__repr__()

    @classmethod
    def from_db(cls, db, field_names, values):
        """ Executed each time a Service is restored from DB layer"""
        instance = super(HasAdaptorClazzMixin, cls).from_db(db, field_names, values)
        # instance._clazz = instance.clazz
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

    def clean(self):
        names = AdaptorLoader.get_class_names()
        if self.clazz and self.clazz not in names:
            raise ValidationError('The class [{}] not configured as ADAPTORS_CLASSES {}'.format(self.clazz, names))

