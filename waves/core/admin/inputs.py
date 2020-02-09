""" Submission Polymorphic Inputs models Admin """

import json

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.db import models, DatabaseError
from django.http import HttpResponseRedirect
from django.template.response import SimpleTemplateResponse
from django.urls import reverse
from django.utils import six
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.http import urlquote
from polymorphic.admin import PolymorphicChildModelFilter, PolymorphicChildModelAdmin, PolymorphicParentModelAdmin

from waves.core.admin.base import WavesModelAdmin
from waves.core.admin.submissions import FileInputSampleInline, SampleDependentInputInline
from waves.core.models import Submission
from waves.core.models.inputs import AParam, FileInput, BooleanParam, ListParam, IntegerParam, DecimalParam, \
    RepeatedGroup, TextParam



__all__ = ['AllParamModelAdmin']

required_base_fields = ['label', 'name', 'cmd_format', 'required', 'submission']
extra_base_fields = ['help_text', 'multiple', 'api_name', 'default']
dependencies_fields = ['parent', 'when_value']


class AParamAdmin(WavesModelAdmin, PolymorphicChildModelAdmin):
    """ Base Input admin """
    base_model = AParam
    exclude = ['order', 'repeat_group']
    readonly_fields = []
    _object = None

    fieldsets = [
        ('General', {
            'fields': required_base_fields,
            'classes': ['collapse', 'open']
        }),
        ('More', {
            'fields': extra_base_fields,
            'classes': ['collapse']
        }),
        ('Dependencies', {
            'fields': dependencies_fields,
            'classes': ['collapse']
        }),
    ]

    @property
    def popup_response_template(self):
        if 'jet' in settings.INSTALLED_APPS:
            return 'waves/admin/baseparam/jet_popup_response.html'
        else:
            return 'waves/admin/baseparam/popup_response.html'

    def get_model_perms(self, request):
        return {}  # super(AllParamModelAdmin, self).get_model_perms(request)

    def get_object(self, request, object_id, from_field=None):
        self._object = super(AParamAdmin, self).get_object(request, object_id, from_field)
        return self._object

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
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
        except DatabaseError as e:
            messages.error(request, "Error occurred saving param %s" % e.message)
            pass
        else:
            messages.success(request, "Param successfully saved")

    def get_form(self, request, obj=None, **kwargs):
        request.current_obj = obj
        form = super(AParamAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['parent'].widget.can_add_related = False
        form.base_fields['parent'].widget.can_change_related = False
        form.base_fields['parent'].widget.can_delete_related = False
        # TODO reactivate repeat_group v1.1.7
        # form.base_fields['repeat_group'].widget.can_add_related = False
        # form.base_fields['repeat_group'].widget.can_change_related = False
        # form.base_fields['repeat_group'].widget.can_delete_related = False
        form.base_fields['submission'].widget = forms.HiddenInput()
        if request.submission or (obj and obj.submission):
            form.base_fields['submission'].initial = request.submission.pk if request.submission else obj.submission.pk
        return form

    def add_view(self, request, form_url='', extra_context=None):
        if IS_POPUP_VAR in request.GET:
            request.submission = Submission.objects.get(pk=request.GET.get('for-submission'))
        else:
            request.submission = None
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
                # noinspection PyProtectedMember
                attr = obj._meta.pk.attname
            value = obj.serializable_value(attr)
            popup_response_data = json.dumps({
                'value': six.text_type(value),
                'obj': six.text_type(obj),
            })
            return SimpleTemplateResponse(self.popup_response_template, context={
                'popup_response_data': popup_response_data
            })
        elif "_addanother" in request.POST:
            pass
        else:
            post_url_continue = reverse('admin:wcore_submission_change', args=[obj.submission.id])
        return super(AParamAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if IS_POPUP_VAR in request.POST:
            to_field = request.POST.get(TO_FIELD_VAR)
            # noinspection PyProtectedMember
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
            return SimpleTemplateResponse(self.popup_response_template, {
                'popup_response_data': popup_response_data,
            })
        elif "_addanother" in request.POST:
            pass
        else:
            # noinspection PyProtectedMember
            opts = self.model._meta
            msg_dict = {
                'name': force_text(opts.verbose_name),
                'obj': format_html('<a href="{}">{}</a>', urlquote(request.path), obj),
            }

            msg = format_html(
                'The {name} "{obj}" was changed successfully.',
                **msg_dict
            )
            self.message_user(request, msg, messages.SUCCESS)
            return HttpResponseRedirect(
                reverse('admin:wcore_submission_change', args=[obj.submission.pk]) + '#/tab/inline_0/')
        return super(AParamAdmin, self).response_change(request, obj)


@admin.register(FileInput)
class FileInputAdmin(AParamAdmin):
    """ FileInput subclass Admin """
    base_model = FileInput
    show_in_index = False
    extra_fieldset_title = 'File params'

    inlines = [FileInputSampleInline, SampleDependentInputInline]
    fieldsets = [
        ('General', {
            'fields': required_base_fields + ['allow_copy_paste', 'max_size', 'allowed_extensions'],
            'classes': ['collapse', 'open']
        }),
        ('More', {
            'fields': extra_base_fields + ['edam_formats', 'edam_datas', 'regexp'],
            'classes': ['collapse']
        }),
        ('Dependencies', {
            'fields': dependencies_fields,
            'classes': ['collapse']
        }),
    ]


@admin.register(TextParam)
class TextParamAdmin(AParamAdmin):
    """ BaseParam subclass Admin """
    base_model = TextParam
    extra_fieldset_title = 'Text input params'
    fieldsets = [
        ('General', {
            'fields': required_base_fields + ['max_length'],
            'classes': ['collapse', 'open']
        }),
        ('More', {
            'fields': extra_base_fields,
            'classes': ['collapse', 'open']
        }),
        ('Dependencies', {
            'fields': dependencies_fields,
            'classes': ['collapse']
        }),
    ]


@admin.register(BooleanParam)
class BooleanParamAdmin(AParamAdmin):
    """ BooleanParam subclass Admin """
    base_model = BooleanParam
    extra_fieldset_title = 'Boolean params'
    fieldsets = [
        ('General', {
            'fields': required_base_fields + ['true_value', 'false_value'],
            'classes': ['collapse', 'open']
        }),
        ('More', {
            'fields': extra_base_fields,
            'classes': ['collapse']
        }),
        ('Dependencies', {
            'fields': dependencies_fields,
            'classes': ['collapse']
        }),
    ]


@admin.register(ListParam)
class ListParamAdmin(AParamAdmin):
    """ ListParam subclass Admin """
    base_model = ListParam
    show_in_index = False
    # fields = ('list_mode', 'list_elements')
    extra_fieldset_title = 'List params'
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 2, 'cols': 50, 'class': 'span8'})}
    }
    fieldsets = [
        ('General', {
            'fields': required_base_fields + ['list_mode', 'list_elements'],
            'classes': ['collapse', 'open']
        }),
        ('More', {
            'fields': extra_base_fields,
            'classes': ['collapse']
        }),
        ('Dependencies', {
            'fields': dependencies_fields,
            'classes': ['collapse']
        })
    ]


@admin.register(IntegerParam)
class IntegerParamAdmin(AParamAdmin):
    """ IntegerParam subclass Admin """
    base_model = IntegerParam
    extra_fieldset_title = 'Integer range'

    fieldsets = [
        ('General', {
            'fields': required_base_fields,
            'classes': ['collapse', 'open']
        }),
        ('More', {
            'fields': extra_base_fields + ['min_val', 'max_val', 'step'],
            'classes': ['collapse']
        }),
        ('Dependencies', {
            'fields': dependencies_fields,
            'classes': ['collapse']
        }),
    ]


@admin.register(DecimalParam)
class DecimalParamAdmin(AParamAdmin):
    """ DecimalParam subclass Admin """

    base_model = DecimalParam
    extra_fieldset_title = 'Decimal range'
    fieldsets = [
        ('General', {
            'fields': required_base_fields,
            'classes': ['collapse', 'open']
        }),
        ('More', {
            'fields': extra_base_fields + ['min_val', 'max_val', 'step'],
            'classes': ['collapse']
        }),
        ('Dependencies', {
            'fields': dependencies_fields,
            'classes': ['collapse']
        }),
    ]


@admin.register(AParam)
class AllParamModelAdmin(PolymorphicParentModelAdmin):
    """ Main polymorphic params Admin """
    base_model = AParam
    exclude = ('order',)
    child_models = (
        TextParam,
        FileInput,
        BooleanParam,
        DecimalParam,
        IntegerParam,
        ListParam,
    )
    list_filter = (PolymorphicChildModelFilter, 'submission', 'submission__service')
    list_display = ('get_class_label', 'label', 'name', 'submission')

    def get_model_perms(self, request):
        return {}  # super(AllParamModelAdmin, self).get_model_perms(request)

    def get_class_label(self, obj):
        return obj.get_real_instance_class().class_label

    get_class_label.short_description = 'Parameter type'

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
