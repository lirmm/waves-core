""" Submission Polymorphic Inputs models Admin """
from __future__ import unicode_literals

import json

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.template.response import SimpleTemplateResponse
from django.utils import six
from polymorphic.admin import PolymorphicChildModelFilter
from polymorphic_tree.admin import PolymorphicMPTTParentModelAdmin, PolymorphicMPTTChildModelAdmin
from waves.admin.submissions import FileInputSampleInline, SampleDependentInputInline
from waves.models.inputs import *
from waves.models.submissions import Submission

__all__ = ['AllParamModelAdmin']


class AParamAdmin(PolymorphicMPTTChildModelAdmin):
    """ Base Input admin """
    base_model = AParam
    exclude = ['order', 'repeat_group']

    base_fieldsets = (
        ('General', {
            'fields': ('label', 'name', 'api_name', 'cmd_format', 'default', 'required', 'submission'),
            'classes': []
        }),
        ('Details', {
            'fields': ('help_text', 'regexp', 'edam_formats', 'edam_datas', 'multiple'),
            'classes': ['collapse']
        }),
        ('Dependencies', {
            'fields': ('parent', 'when_value'),
            'classes': ['collapse']
        }),
    )
    # TODO NEXT VERSION
    """
    ('Grouping', {
        'fields': ('repeat_group',),
        'classes': ['collapse']
    })
    """
    readonly_fields = []
    _object = None

    def get_model_perms(self, request):
        return {}  # super(AllParamModelAdmin, self).get_model_perms(request)

    def get_object(self, request, object_id, from_field=None):
        self._object = super(AParamAdmin, self).get_object(request, object_id, from_field)
        return self._object

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # TODO when non popup access disabled, following if would be obsolete
        if request.current_obj:
            if db_field.name == 'repeat_group':
                kwargs['queryset'] = RepeatedGroup.objects.filter(submission=request.current_obj.submission)
            elif db_field.name == "parent":
                kwargs['queryset'] = AParam.objects.filter(submission=request.current_obj.submission).exclude(
                    pk=request.current_obj.pk)
        if request.submission:
            if db_field.name == 'repeat_group':
                kwargs['queryset'] = RepeatedGroup.objects.filter(submission=request.submission)
            elif db_field.name == "parent":
                pk = self._object.pk if self._object else -1
                kwargs['queryset'] = AParam.objects.filter(submission=request.submission).not_instance_of(
                    FileInput).exclude(pk=pk)
            elif db_field.name == 'submission':
                kwargs['queryset'] = Submission.objects.filter(pk=request.submission.pk)
        return super(AParamAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if request.submission:
            obj.submission = request.submission
        try:
            super(AParamAdmin, self).save_model(request, obj, form, change)
        except BaseException:
            pass
        else:
            messages.success(request, "Param successfully saved")

    def get_form(self, request, obj=None, **kwargs):
        request.current_obj = obj
        form = super(AParamAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['parent'].widget.can_add_related = False
        form.base_fields['parent'].widget.can_change_related = False
        form.base_fields['parent'].widget.can_delete_related = False
        # TODO reactivate repeat_group management from inside inputs
        # form.base_fields['repeat_group'].widget.can_add_related = False
        # form.base_fields['repeat_group'].widget.can_change_related = False
        # form.base_fields['repeat_group'].widget.can_delete_related = False
        form.base_fields['submission'].widget = forms.HiddenInput()
        if request.submission or (obj and obj.submission):
            form.base_fields['submission'].initial = request.submission.pk if request.submission else obj.submission.pk
        # form.fields['submission'].initial = request.submission
        return form

    def add_view(self, request, form_url='', extra_context=None):
        if IS_POPUP_VAR in request.GET:
            request.submission = Submission.objects.get(pk=request.GET.get('for-submission'))
        else:
            request.submission = None
        # TODO add error message, can't edit this object outside popup
        return super(AParamAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        request.submission = AParam.objects.get(pk=object_id).submission
        return super(AParamAdmin, self).change_view(request, object_id, form_url, extra_context)

    def get_readonly_fields(self, request, obj=None):
        return super(AParamAdmin, self).get_readonly_fields(request, obj)

    def get_prepopulated_fields(self, request, obj=None):
        return super(AParamAdmin, self).get_prepopulated_fields(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        if IS_POPUP_VAR in request.POST:
            to_field = request.POST.get(TO_FIELD_VAR)
            if to_field:
                attr = str(to_field)
            else:
                attr = obj._meta.pk.attname
            value = obj.serializable_value(attr)
            popup_response_data = json.dumps({
                'value': six.text_type(value),
                'obj': six.text_type(obj),
            })
            return SimpleTemplateResponse('admin/waves/baseparam/popup_response.html', {
                'popup_response_data': popup_response_data,
            })
        return super(AParamAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if IS_POPUP_VAR in request.POST:
            to_field = request.POST.get(TO_FIELD_VAR)
            attr = str(to_field) if to_field else obj._meta.pk.attname
            # Retrieve the `object_id` from the resolved pattern arguments.
            value = request.resolver_match.args[0]
            new_value = obj.serializable_value(attr)
            popup_response_data = json.dumps({
                'action': 'change',
                'value': six.text_type(value),
                'obj': six.text_type(obj),
                'new_value': six.text_type(new_value),
            })
            return SimpleTemplateResponse('admin/waves/baseparam/popup_response.html', {
                'popup_response_data': popup_response_data,
            })
        return super(AParamAdmin, self).response_change(request, obj)


@admin.register(FileInput)
class FileInputAdmin(AParamAdmin):
    """ FileInput subclass Admin """
    base_model = FileInput
    show_in_index = False
    extra_fieldset_title = 'File params'

    inlines = [FileInputSampleInline]
    # TODO activate sample selection dependencies (both on forms and on submission)
    # TOD, SampleDependentInputInline,]
    readonly_fields = ['regexp',]


@admin.register(TextParam)
class TextParamAdmin(AParamAdmin):
    """ BaseParam subclass Admin """
    base_model = TextParam



@admin.register(BooleanParam)
class BooleanParamAdmin(AParamAdmin):
    """ BooleanParam subclass Admin """
    base_model = BooleanParam
    extra_fieldset_title = 'Boolean params'


@admin.register(ListParam)
class ListParamAdmin(AParamAdmin):
    """ ListParam subclass Admin """
    base_model = ListParam
    show_in_index = False
    # fields = ('list_mode', 'list_elements')
    extra_fieldset_title = 'List params'


@admin.register(IntegerParam)
class IntegerParamAdmin(AParamAdmin):
    """ IntegerParam subclass Admin """
    base_model = IntegerParam
    extra_fieldset_title = 'Integer range'


@admin.register(DecimalParam)
class DecimalParamAdmin(AParamAdmin):
    """ DecimalParam subclass Admin """

    base_model = DecimalParam
    extra_fieldset_title = 'Decimal range'


@admin.register(AParam)
class AllParamModelAdmin(PolymorphicMPTTParentModelAdmin):
    """ Main polymorphic params Admin """
    base_model = AParam

    child_models = (
        (FileInput, FileInputAdmin),
        (BooleanParam, BooleanParamAdmin),
        (DecimalParam, DecimalParamAdmin),
        (IntegerParam, IntegerParamAdmin),
        (ListParam, ListParamAdmin),
        (TextParam, TextParamAdmin)
    )
    list_filter = (PolymorphicChildModelFilter, 'submission', 'submission__service')
    list_display = ('get_class_label', 'label', 'name', 'submission')


    def get_model_perms(self, request):
        return {}  # super(AllParamModelAdmin, self).get_model_perms(request)

    def get_class_label(self, obj):
        return obj.get_real_instance_class().class_label

    get_class_label.short_description = 'Parameter type'

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        return super(AllParamModelAdmin, self).changeform_view(request, object_id, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return super(AllParamModelAdmin, self).change_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        from django.contrib.admin.options import IS_POPUP_VAR
        if IS_POPUP_VAR in request.POST:
            pass
        return super(AllParamModelAdmin, self).response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        from django.contrib.admin.options import IS_POPUP_VAR
        if IS_POPUP_VAR in request.POST:
            pass
        return super(AllParamModelAdmin, self).response_add(request, obj, post_url_continue)
