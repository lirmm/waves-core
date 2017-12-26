""" All Input related models """
from __future__ import unicode_literals

from decimal import Decimal
from os.path import basename

import swapper
from django.core.exceptions import ValidationError
from django.db import models
from django import forms
from django.utils.safestring import mark_safe
from polymorphic.models import PolymorphicModel, PolymorphicManager

from waves.wcore.models.base import WavesBaseModel, Ordered, ApiModel
from waves.wcore.settings import waves_settings
from waves.wcore.utils.storage import file_sample_directory, waves_storage
from waves.wcore.utils.validators import validate_list_comma, validate_list_param
from waves.wcore.models.const import *

__all__ = ['AParam', 'RepeatedGroup', 'FileInput', 'BooleanParam', 'DecimalParam', 'NumberParam',
           'ListParam', 'IntegerParam', 'TextParam', 'FileInputSample', 'SampleDepParam']


class RepeatedGroup(Ordered):
    """ Some input may be grouped, and group could be repeated"""

    submission = models.ForeignKey(swapper.get_model_name('wcore', 'Submission'),
                                   related_name='submission_groups', null=True,
                                   on_delete=models.CASCADE)
    name = models.CharField('Group name', max_length=50, null=False, blank=False)
    title = models.CharField('Group title', max_length=200, null=False, blank=False)
    max_repeat = models.IntegerField("Max repeat", null=True, blank=True)
    min_repeat = models.IntegerField('Min repeat', default=0)
    default = models.IntegerField('Default repeat', default=0)

    def __str__(self):
        return '[%s]' % self.name


class AParam(PolymorphicModel, ApiModel, Ordered):
    class Meta:
        verbose_name_plural = "Inputs"
        verbose_name = "Input"
        base_manager_name = 'base_objects'
        ordering = ('order',)

    objects = PolymorphicManager()
    # order = models.PositiveIntegerField('Ordering in forms', default=0)
    #: Input Label
    label = models.CharField('Label', max_length=100, blank=False, null=False, help_text='Input displayed label')
    #: Input submission name
    name = models.CharField('Parameter name', max_length=50, blank=False, null=False,
                            help_text='Input runner\'s job param command line name')
    multiple = models.BooleanField('Multiple', default=False, help_text="Can hold multiple values")
    help_text = models.TextField('Help Text', null=True, blank=True)
    submission = models.ForeignKey(swapper.get_model_name('wcore', 'Submission'), on_delete=models.CASCADE, null=False,
                                   related_name='inputs')
    required = models.NullBooleanField('Required', choices={(False, "Optional"), (True, "Required"),
                                                            (None, "Not submitted by user")},
                                       default=True, help_text="Submitted and/or Required")
    default = models.CharField('Default value', max_length=50, null=True, blank=True)
    cmd_format = models.IntegerField('Command line format', choices=OPT_TYPE,
                                     default=OPT_TYPE_SIMPLE,
                                     help_text='Command line pattern')
    edam_formats = models.CharField('Edam format(s)', max_length=255, null=True, blank=True,
                                    help_text="comma separated list of supported edam format")
    edam_datas = models.CharField('Edam data(s)', max_length=255, null=True, blank=True,
                                  help_text="comma separated list of supported edam data param_type")
    repeat_group = models.ForeignKey(RepeatedGroup, null=True, blank=True, on_delete=models.SET_NULL,
                                     help_text="Group and repeat items")
    """ Main class for Basic data related to Service submissions inputs """
    class_label = "Basic"
    # Submission params dependency
    when_value = models.CharField('When value', max_length=255, null=True, blank=True,
                                  help_text='Input is treated only for this parent value')
    parent = models.ForeignKey('self', related_name="dependents_inputs", on_delete=models.CASCADE,
                               null=True, blank=True, help_text='Input is associated to')
    regexp = models.CharField('Validation Regexp', max_length=255, null=True, blank=True)

    command_line_value = "-user_value-"

    def save(self, *args, **kwargs):
        if self.parent is not None and self.required is True:
            self.required = False
        if self.repeat_group is not None:
            self.multiple = True
        if not self.order:
            self.order = AParam.objects.filter(submission=self.submission).count() + 1
        super(AParam, self).save(*args, **kwargs)

    def duplicate_api_name(self, api_name):
        """ Check is another entity is set with same api_name for the same submission

        :param api_name:
        """
        return AParam.objects.filter(api_name=api_name, submission=self.submission).exclude(pk=self.pk)

    @property
    def related_to(self):
        return self.parent

    @property
    def type(self):
        """ Backward compatibility with old property """
        return self.param_type

    def check_when_value(self, value):
        return True

    @property
    def param_type(self):
        return TYPE_TEXT

    def clean(self):
        if self.required is None and not self.default and self.cmd_format not in (
                OPT_TYPE_NAMED_OPTION, OPT_TYPE_OPTION, OPT_TYPE_NONE):
            # param is mandatory
            raise ValidationError('Not displayed parameters must have a default value %s:%s' % (self.name, self.label))
        if self.parent and not self.when_value:
            raise ValidationError({'when_value': 'If you set a dependency, you must set this value'})
        if self.parent is not None:
            self.parent.check_when_value(self.when_value)
        for dep in self.dependents_inputs.all():
            if (isinstance(self, ListParam) or isinstance(self, BooleanParam)) and dep.when_value not in self.values:
                raise ValidationError('Input "%s" depends on missing value: \'%s\'  ' % (dep.label, dep.when_value))

    def __str__(self):
        return self.label + ' (' + self.__class__.__name__ + ')'

    @property
    def mandatory(self):
        return self.required is True

    @property
    def format(self):
        return ""

    @property
    def value(self):
        return "%s_value" % self.name

    def field_dict(self, data=None):
        return dict(
            label=self.label,
            required=self.mandatory,
            help_text=self.help_text,
            initial=data if data else self.default
        )

    def form_widget(self, data=None):
        return {self.api_name: forms.CharField(**self.field_dict(data))}


class TextParam(AParam):
    class Meta:
        verbose_name = "Text Input"
        verbose_name_plural = "Text Input"

    max_length = models.CharField('Max length (<255)', max_length=255, default=255)

    @property
    def param_type(self):
        return TYPE_TEXT

    def field_dict(self, data=None):
        initial = super(TextParam, self).field_dict(data)
        initial.update(dict(max_length=self.max_length))
        return initial


class BooleanParam(AParam):
    """ Boolean param (usually check box for a submission option)"""

    class Meta:
        verbose_name = "Boolean choice"
        verbose_name_plural = "Boolean choices"

    class_label = "Boolean"
    true_value = models.CharField('True value', default='True', max_length=50)
    false_value = models.CharField('False value', default='False', max_length=50)

    @property
    def param_type(self):
        return TYPE_BOOLEAN

    @property
    def choices(self):
        try:
            return [(None, '----'),
                    (self.true_value, True),
                    (self.false_value, False)]
        except ValueError:
            raise RuntimeError('Wrong list element format')

    @property
    def labels(self):
        return []

    @property
    def values(self):
        return [self.true_value, self.false_value]

    def check_when_value(self, value):
        if value not in self.values:
            raise ValidationError({'when_value': 'This value is not possible for related input [%s]' % ', '.join(
                self.values)})

    def form_widget(self, data=None):
        return {self.api_name: forms.BooleanField(**self.field_dict(data))}


class NumberParam(object):
    """ Abstract Base class for 'number' validation """

    class Meta:
        proxy = True
        abstract = True

    def clean(self):
        super(NumberParam, self).clean()
        if self.default:
            raises = False
            min_val = self.min_val
            max_val = self.max_val
            if self.min_val is not None and self.max_val is None:
                raises = not (Decimal(self.min_val) <= Decimal(self.default.strip()))
                max_val = '+&infin;'
            elif self.max_val is not None and self.min_val is None:
                raises = not (Decimal(self.default.strip()) <= Decimal(self.max_val))
                min_val = '-&infin;'
            elif self.max_val is not None and self.min_val is not None:
                raises = not (Decimal(self.min_val) <= Decimal(self.default.strip()) <= Decimal(self.max_val))
            if raises:
                raise ValidationError({'default': mark_safe('Default value is not in range [%s, %s]' % (
                    min_val, max_val))})
        if self.min_val and self.max_val:
            if self.min_val > self.max_val:
                raise ValidationError({'min_val': 'Minimum value can\'t exceed maximum value'})
            elif self.min_val == self.max_val:
                raise ValidationError({'min_val': 'Minimum value can\'t equal maximum value'})

    def check_when_value(self, value):
        min_val = self.min_val
        max_val = self.max_val
        raises = False
        if self.min_val is not None and self.max_val is None:
            raises = not (Decimal(self.min_val) <= Decimal(value.strip()))
            max_val = '+&infin;'
        elif self.max_val is not None and self.min_val is None:
            raises = not (Decimal(value.strip()) <= Decimal(self.max_val))
            min_val = '-&infin;'
        elif self.max_val is not None and self.min_val is not None:
            raises = not (Decimal(self.min_val) <= Decimal(value.strip()) <= Decimal(self.max_val))
        if raises:
            raise ValidationError({'when_value': 'This value is not possible for related input range [%s, %s]' % (
                min_val, max_val)})

    def field_dict(self, data=None):
        initial = super(NumberParam, self).field_dict(data)
        initial.update(dict(
            min_value=self.min_val,
            max_value=self.max_val
        ))
        return initial


class DecimalParam(NumberParam, AParam):
    """ Number param (decimal or float) """

    # TODO add specific validator
    class Meta:
        verbose_name = "Decimal"
        verbose_name_plural = "Decimal"

    class_label = "Decimal"
    min_val = models.DecimalField('Min value', decimal_places=3, max_digits=50, default=None, null=True, blank=True,
                                  help_text="Leave blank if no min")
    max_val = models.DecimalField('Max value', decimal_places=3, max_digits=50, default=None, null=True, blank=True,
                                  help_text="Leave blank if no max")
    step = models.DecimalField('Step', decimal_places=3, max_digits=50, default=0.5, null=False, blank=True)

    @property
    def param_type(self):
        return TYPE_DECIMAL

    def form_widget(self, data=None):
        widget = forms.DecimalField(**self.field_dict(data))
        # widget.attrs['step'] = self.step
        return {self.api_name: widget}


class IntegerParam(NumberParam, AParam):
    """ Integer param """

    class Meta:
        # TODO add specific validator
        verbose_name = "Integer"
        verbose_name_plural = "Integer"

    class_label = "Integer"
    min_val = models.IntegerField('Min value', default=0, null=True, blank=True,
                                  help_text="Leave blank if no min")
    max_val = models.IntegerField('Max value', default=None, null=True, blank=True,
                                  help_text="Leave blank if no max")
    step = models.IntegerField('Step', default=1, blank=True, help_text="Step to increment/decrement values")

    @property
    def param_type(self):
        return TYPE_INT

    def form_widget(self, data=None):
        widget = forms.IntegerField(**self.field_dict(data))
        # widget.attrs['step'] = self.step
        return {self.api_name: widget}


class ListParam(AParam):
    """ Param to be issued from a list of values (select / radio / check) """

    class Meta:
        verbose_name = "List"
        verbose_name_plural = "Lists"

    DISPLAY_SELECT = 'select'
    DISPLAY_RADIO = 'radio'
    DISPLAY_CHECKBOX = 'checkbox'
    LIST_DISPLAY_TYPE = [
        (DISPLAY_SELECT, 'Select List'),
        (DISPLAY_RADIO, 'Radio buttons'),
        (DISPLAY_CHECKBOX, 'Check box')
    ]

    class_label = "List"
    list_mode = models.CharField('List display mode', choices=LIST_DISPLAY_TYPE, default=DISPLAY_SELECT,
                                 max_length=100)
    list_elements = models.TextField('Elements', validators=[validate_list_param, ],
                                     help_text="One Element per line label|value")

    def save(self, *args, **kwargs):
        if self.list_mode == ListParam.DISPLAY_CHECKBOX:
            self.multiple = True
        super(ListParam, self).save(*args, **kwargs)

    def clean(self):
        super(ListParam, self).clean()
        if self.list_mode == ListParam.DISPLAY_RADIO and self.multiple:
            raise ValidationError('You can\'t use radio with multiple choices available')
        elif self.list_mode == ListParam.DISPLAY_CHECKBOX and not self.multiple:
            raise ValidationError('You can\'t use checkboxes with non multiple choices enabled')
        if self.default and self.default not in self.values:
            raise ValidationError(
                {'default': 'Default value "%s" is not present in list [%s]' % (self.default, ', '.join(self.values))})

    @property
    def choices(self):
        choice_init = [(None, '----')] if self.list_mode == ListParam.DISPLAY_SELECT and self.required is False else []
        try:
            return choice_init + \
                   [(line.split('|')[1], line.split('|')[0]) for line in self.list_elements.splitlines()]
        except ValueError:
            raise RuntimeError('Wrong list element format')

    @property
    def param_type(self):
        return TYPE_LIST

    @property
    def labels(self):
        return [line.split('|')[0] for line in self.list_elements.splitlines()]

    @property
    def values(self):
        return [line.split('|')[1] for line in self.list_elements.splitlines()]

    def check_when_value(self, value):
        if value not in self.values:
            raise ValidationError({'when_value': 'This value is not possible for related input [%s]' % ', '.join(
                self.values)})

    def field_dict(self, data=None):
        initial = super(ListParam, self).field_dict(data)
        initial.update(dict(
            choices=self.choices,
        ))
        if not self.multiple:
            if self.list_mode == self.DISPLAY_RADIO:
                initial['widget'] = forms.RadioSelect()
        else:
            initial['widget'] = forms.CheckboxSelectMultiple()

        return initial

    def form_widget(self, data=None):
        if self.multiple:
            return {self.api_name: forms.MultipleChoiceField(**self.field_dict(data))}
        return {self.api_name: forms.ChoiceField(**self.field_dict(data))}


class FileInput(AParam):
    """ Submission file inputs """

    class Meta:
        ordering = ['order', ]
        verbose_name = "File input"
        verbose_name_plural = "Files inputs"

    class_label = "File Input"

    max_size = models.BigIntegerField('Allowed file size ', default=waves_settings.UPLOAD_MAX_SIZE / 1024,
                                      help_text="in Ko")
    allowed_extensions = models.CharField('Filter by extensions', max_length=255,
                                          help_text="Comma separated list, * means no filter",
                                          default="*",
                                          validators=[validate_list_comma, ])

    @property
    def param_type(self):
        return TYPE_FILE

    def form_widget(self, data=None):
        initial_fields = self.field_dict(data)
        initial_fields['required'] = False
        initial = {self.api_name: forms.FileField(**initial_fields),
                   'cp_%s' % self.api_name: forms.CharField(label='Copy/paste content',
                                                            required=False,
                                                            widget=forms.Textarea(attrs={'cols': 20, 'rows': 10})
                                                            )}
        for sample in self.input_samples.all():
            initial['sp_%s_%s' % (self.api_name, sample.pk)] = sample.form_widget()
        return initial


class FileInputSample(WavesBaseModel):
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

    def form_widget(self):
        field_dict = dict(
            label=self.label,
            required=False,
            help_text=self.help_text,
            initial=False
        )
        form_field = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'no-switch'}), **field_dict)
        return form_field


class SampleDepParam(WavesBaseModel):
    """
    When a file sample is selected, some params may be set accordingly.
    This class represent this behaviour
    """

    class Meta:
        verbose_name_plural = "Sample dependencies"
        verbose_name = "Sample dependency"

    #: Related file input when sample is selected
    file_input = models.ForeignKey('FileInput', null=True, on_delete=models.CASCADE,
                                   related_name="sample_dependencies")
    #: Related sample File
    sample = models.ForeignKey(FileInputSample, on_delete=models.CASCADE, related_name='dependent_inputs')
    #: Related impacted submission input
    related_to = models.ForeignKey('AParam', on_delete=models.CASCADE, related_name='related_samples')
    #: Value to set in case of Sample selected
    set_default = models.CharField('Set value to ', max_length=200, null=False, blank=False)

    def __str__(self):
        return "%s > %s=%s" % (self.sample.label, self.related_to.name, self.set_default)
