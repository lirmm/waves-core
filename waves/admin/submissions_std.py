from __future__ import unicode_literals

from polymorphic.admin import StackedPolymorphicInline, PolymorphicInlineModelAdmin
from django import forms
from waves.admin.submissions import *


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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parent':
            kwargs['queryset'] = AParam.objects.filter(submission=request.current_obj)
        return super(AParamInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class FileInputInline(AParamInline):
    fields = required_base_fields + ['max_size', 'allowed_extensions'] + extra_base_fields
    exclude = ['order']
    model = FileInput
    form = OrganizeInputForm


class IntegerFieldInline(AParamInline):
    fields = required_base_fields + extra_base_fields + ['min_val', 'max_val', 'step']
    exclude = ['order']
    model = IntegerParam
    form = OrganizeInputForm


class BooleanFielInline(AParamInline):
    fields = required_base_fields + ['true_value', 'false_value'] + extra_base_fields
    exclude = ['order']
    model = BooleanParam
    form = OrganizeInputForm


class TextFieldInline(AParamInline):
    fields = required_base_fields + extra_base_fields
    model = AParam
    exclude = ['order']
    form = TextParamForm


class DecimalFieldInline(AParamInline):
    fields = required_base_fields + extra_base_fields + ['min_val', 'max_val', 'step']
    exclude = ['order']
    model = DecimalParam
    form = OrganizeInputForm


class ListFieldInline(AParamInline):
    fields = required_base_fields + ['list_mode', 'list_elements'] + extra_base_fields
    exclude = ['order']
    model = ListParam
    form = OrganizeInputForm


class OrganizeInputInline(StackedPolymorphicInline):
    """
    An inline for a polymorphic model.
    The actual form appearance of each row is determined by
    the child inline that corresponds with the actual model type.
    """
    _submission_instance = None

    model = AParam
    child_inlines = (
        FileInputInline,
        DecimalFieldInline,
        IntegerFieldInline,
        BooleanFielInline,
        ListFieldInline,
        TextFieldInline
    )
    classes = ["collapse", ]
