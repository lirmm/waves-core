from __future__ import unicode_literals

from django import forms
from polymorphic.admin import StackedPolymorphicInline
from waves.wcore.models.inputs import *


class OrganizeInputForm(forms.ModelForm):
    class Meta:
        model = AParam
        exclude = ['pk']

    def __init__(self, *args, **kwargs):
        super(OrganizeInputForm, self).__init__(*args, **kwargs)
        self.fields['parent'].widget.can_add_related = False
        self.fields['parent'].widget.can_change_related = False


class TextParamForm(OrganizeInputForm):
    class Meta:
        model = TextParam
        exclude = ['order']


required_base_fields = ['label', 'name', 'cmd_format']
extra_base_fields = ['help_text', 'required', 'api_name', 'default', 'parent', 'when_value']


class AParamInline(StackedPolymorphicInline.Child):
    classes = ['collapse', ]
    model = AParam

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parent':
            kwargs['queryset'] = AParam.objects.filter(submission=request.current_obj)
        return super(AParamInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

    fieldsets = [
        ('General', {
            'fields': required_base_fields,
            'classes': ['']
        }),
        ('Details', {
            'fields': extra_base_fields,
            'classes': ['collapse']
        }),
    ]


class TextParamInline(AParamInline):
    fields = required_base_fields + ['max_length'] + extra_base_fields
    exclude = ['order']
    classes = ['collapse']
    model = TextParam
    form = OrganizeInputForm

    fieldsets = [
        ('General', {
            'fields': required_base_fields,
            'classes': ['']
        }),
        ('Details', {
            'fields': extra_base_fields,
            'classes': ['collapse']
        }),
        ('Text params', {
            'fields': ['max_length', ],
            'classes': ['collapse']
        }),
    ]


class FileInputInline(AParamInline):
    fields = required_base_fields + ['max_size', 'allowed_extensions', 'regexp'] + extra_base_fields
    exclude = ['order']
    classes = ['collapse']
    model = FileInput
    form = OrganizeInputForm

    fieldsets = [
        ('General', {
            'fields': required_base_fields,
            'classes': ['']
        }),
        ('Details', {
            'fields': extra_base_fields,
            'classes': ['collapse']
        }),
        ('File set up', {
            'fields': ['max_size', 'allowed_extensions', 'regexp'],
            'classes': ['collapse']
        }),
    ]


class IntegerFieldInline(AParamInline):
    fields = required_base_fields + extra_base_fields + ['min_val', 'max_val', 'step']
    exclude = ['order']
    model = IntegerParam
    form = OrganizeInputForm

    fieldsets = [
        ('General', {
            'fields': required_base_fields,
            'classes': ['']
        }),
        ('Details', {
            'fields': extra_base_fields,
            'classes': ['collapse']
        }),
        ('Integer range params', {
            'fields': ['min_val', 'max_val', 'step'],
            'classes': ['collapse']
        }),
    ]


class BooleanFieldInline(AParamInline):
    fields = required_base_fields + ['true_value', 'false_value'] + extra_base_fields
    exclude = ['order']
    model = BooleanParam
    form = OrganizeInputForm

    fieldsets = [
        ('General', {
            'fields': required_base_fields,
            'classes': ['']
        }),
        ('Details', {
            'fields': extra_base_fields,
            'classes': ['collapse']
        }),
        ('Boolean params', {
            'fields': ['true_value', 'false_value'],
            'classes': ['collapse']
        }),
    ]


class DecimalFieldInline(AParamInline):
    fields = required_base_fields + extra_base_fields + ['min_val', 'max_val', 'step']
    exclude = ['order']
    model = DecimalParam
    form = OrganizeInputForm

    fieldsets = [
        ('General', {
            'fields': required_base_fields,
            'classes': ['']
        }),
        ('Details', {
            'fields': extra_base_fields,
            'classes': ['collapse']
        }),
        ('Decimal range params', {
            'fields': ['min_val', 'max_val', 'step'],
            'classes': ['collapse']
        }),
    ]


class ListFieldInline(AParamInline):
    fields = required_base_fields + ['list_mode', 'list_elements'] + extra_base_fields
    exclude = ['order']
    model = ListParam
    form = OrganizeInputForm

    fieldsets = [
        ('General', {
            'fields': required_base_fields,
            'classes': ['']
        }),
        ('Details', {
            'fields': extra_base_fields,
            'classes': ['collapse']
        }),
        ('List params', {
            'fields': ['list_mode', 'list_elements'],
            'classes': ['collapse']
        }),
    ]


class OrganizeInputInline(StackedPolymorphicInline):
    """
    An inline for a polymorphic model.
    The actual form appearance of each row is determined by
    the child inline that corresponds with the actual model type.
    """
    _submission_instance = None

    model = AParam
    child_inlines = (
        TextParamInline,
        FileInputInline,
        DecimalFieldInline,
        IntegerFieldInline,
        BooleanFieldInline,
        ListFieldInline,
    )
    classes = ["collapse", ]

    base_fieldsets = [
        ('General', {
            'fields': required_base_fields,
            'classes': ['']
        }),
        ('Details', {
            'fields': extra_base_fields,
            'classes': ['collapse']
        })
    ]

