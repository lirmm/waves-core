""" Django models bases classes """

import re
import uuid

import inflection
from django.core.exceptions import ObjectDoesNotExist, ValidationError, MultipleObjectsReturned
from django.db import models

from waves.core.compat import RichTextField
from waves.core.settings import waves_settings

__all__ = ['TimeStamped', 'Ordered', 'ExportAbleMixin', 'Described', 'Slugged', 'ApiModel',
           'UrlMixin', 'ExportError']


class TimeStamped(models.Model):
    """
    Time stamped 'able' models objects, add fields to inherited objects

    .. note::
        This class add also default ordering by -updated, -created (reverse order)

    """

    class Meta:
        abstract = True
        ordering = ['-updated', '-created']

    #: (auto_now_add): set when model object is created
    created = models.DateTimeField('Created on', auto_now_add=True, editable=False, help_text='Creation timestamp')
    #: (auto_now): set each time model object is saved in database
    updated = models.DateTimeField('Last Update', auto_now=True, editable=False, help_text='Last update timestamp')


class Ordered(models.Model):
    """ Order-able models objects,

    .. note::
        Default ordering field is set to 'order'
    """

    class Meta:
        abstract = True
        ordering = ['order']

    #: positive integer field (default to 0)
    order = models.PositiveIntegerField(default=0, blank=False, null=False)


class Described(models.Model):
    """
    A model object which inherit from this class add two description fields to model objects

    """

    class Meta:
        abstract = True

    #: Text field to set up a complete description of model object, with HTML editor enabled
    description = RichTextField('Description', null=True, blank=True, help_text='Description (HTML)')
    #: text field for short version, no html
    short_description = models.TextField('Short Description', null=True, blank=True,
                                         help_text='Short description (Text)')


class Slugged(models.Model):
    """ Add a 'slug' field to models Objects, based on uuid.uuid4 field generator, this field is mainly used for models
    objects urls
    """

    class Meta:
        abstract = True

    #: UUID field is base on uuid4 generator.
    slug = models.UUIDField(default=uuid.uuid4, blank=True, unique=True, editable=False)


class ApiModel(models.Model):
    """
    An API-able model object need a 'api_name', in order to setup dedicated url for this model object
    """

    class Meta:
        abstract = True

    #: Default field use to generate a api_name (unique app name)
    field_api_name = 'name'
    #: A char field, must be unique for a model instance
    api_name = models.CharField(verbose_name="App short code", max_length=100, null=True, blank=True,
                                help_text='App short code, used in url, leave blank for automatic setup')

    @property
    def base_api_name(self):
        last_pos = self.api_name.rfind('_')
        if last_pos != -1 and self.api_name[last_pos + 1:].isdigit():
            return self.api_name[:last_pos + 1]
        else:
            return self.api_name

    def duplicate_api_name(self, api_name):
        """ Check is another entity is set with same api_name

        :param api_name: checked api name
        """
        return self.__class__.objects.filter(api_name=api_name).exclude(pk=self.pk)

    def _create_api_name(self):
        """
        Construct a new wapi:v2 name issued from field_api_name
        """
        return inflection.underscore(re.sub(r'[^\w]+', '_', getattr(self, self.field_api_name))).lower()

    def clean(self):
        try:
            if self.duplicate_api_name(self.api_name).count() > 0:
                raise ValidationError({'api_name': 'Value must be unique'})
        except MultipleObjectsReturned:
            raise ValidationError({'api_name': "Value is not unique"})
        except ObjectDoesNotExist:
            pass


class UrlMixin(object):
    """ Url Mixin allow easy generation or absolute url related to any model object

    .. note::
       Sub-classes must define a get_absolute_url() method > See
       `Django get_absolute_url <https://docs.djangoproject.com/en/1.9/ref/models/instances/#get-absolute-url>`_
    """

    @property
    def link(self):
        """ short cut to :func:`get_url()`
        :return: current absolute uri for Job
        """
        return "{}{}".format(waves_settings.HOST, self.get_absolute_url())

    def get_url(self):
        """ Calculate and return absolute 'front-office' url for a model object
        :return: unicode the absolute url
        """
        return self.get_absolute_url()

    def get_absolute_url(self):
        raise NotImplementedError


class ExportError(Exception):
    """ Export 'Error'"""
    pass


class ExportAbleMixin(object):
    """ Some models object may be 'exportable' in order to be imported elsewhere in another WAVES app.
    Based on Django serializer, because we don't want to select fields to export
    """

    @property
    def serializer(self, context=None):
        """ Each sub class must implement this method to initialize its Serializer"""
        raise NotImplementedError('Sub classes must implements this method')

    def serialize(self):
        """ Import model object serializer, serialize and write data to disk """
        from os.path import join
        from os import mkdir, listdir
        from waves.core.settings import waves_settings
        import json
        if 'export' not in listdir(waves_settings.DATA_ROOT):
            mkdir(join(waves_settings.DATA_ROOT, 'export'))
        file_path = join(waves_settings.DATA_ROOT, 'export', self.export_file_name)
        with open(file_path, 'w') as fp:
            try:
                serializer = self.serializer()
                data = serializer.to_representation(self)
                fp.write(json.dumps(data, indent=2))
                return file_path
            except Exception as e:
                raise ExportError('Error dumping model {} [{}]'.format(self, e))

    @property
    def export_file_name(self):
        """ Create export file name, based on concrete class name"""
        return '{}_{}.json'.format(self.__class__.__name__.lower(), str(self.pk))
