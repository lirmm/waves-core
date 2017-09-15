""" Service Submission administration classes """
from __future__ import unicode_literals

from adminsortable2.admin import SortableInlineAdminMixin
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from polymorphic.admin import PolymorphicInlineSupportMixin

from waves.wcore.admin.adaptors import SubmissionRunnerParamInLine
from waves.wcore.admin.base import WavesModelAdmin, DynamicInlinesAdmin
from waves.wcore.admin.forms.services import *
from waves.wcore.compat import CompactInline
from waves.wcore.models.inputs import *
from waves.wcore.models.services import Submission, SubmissionOutput, SubmissionExitCode

__all__ = ['SubmissionOutputInline', 'SampleDependentInputInline', 'ExitCodeInline', 'FileInputSampleInline',
           'RepeatGroupAdmin', 'OrgRepeatGroupInline', 'ServiceSubmissionAdmin']


class SubmissionOutputInline(CompactInline):
    """ Service Submission Outputs Inlines """
    model = SubmissionOutput
    form = SubmissionOutputForm
    show_change_link = False
    extra = 0
    sortable_field_name = "order"
    sortable_options = []
    fk_name = 'submission'
    # fields = ['label', 'file_pattern', 'api_name', 'extension', 'edam_format', 'edam_data', 'from_input', 'help_text']
    verbose_name_plural = "Outputs"
    classes = ('grp-collapse', 'grp-closed', 'collapse')

    fieldsets = [
        ('General', {
            'fields': ['label', 'file_pattern', 'extension'],
            'classes': ['collapse', 'open']
        }),
        ('More', {
            'fields': ['api_name', 'edam_format', 'edam_data', 'from_input', 'help_text'],
            'classes': ['collapse']
        }),
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "from_input":
            kwargs['queryset'] = AParam.objects.filter(submission=request.current_obj)
        return super(SubmissionOutputInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class SampleDependentInputInline(CompactInline):
    model = SampleDepParam
    form = SampleDepForm
    fk_name = 'file_input'
    extra = 0
    classes = ('grp-collapse grp-closed', 'collapse')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "related_to" and request.current_obj is not None:
            kwargs['queryset'] = AParam.objects.filter(submission=request.current_obj.submission,
                                                       cmd_format__gt=0).not_instance_of(FileInput)
        return super(SampleDependentInputInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class SampleDependentInputInline2(CompactInline):
    model = SampleDepParam
    form = SampleDepForm2
    fk_name = 'sample'
    extra = 0
    classes = ('grp-collapse grp-closed', 'collapse')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "related_to":
            kwargs['queryset'] = AParam.objects.filter(cmd_format__gt=0).not_instance_of(FileInput)
        return super(SampleDependentInputInline2, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ExitCodeInline(admin.TabularInline):
    model = SubmissionExitCode
    extra = 0
    fk_name = 'submission'
    is_nested = False
    classes = ('grp-collapse grp-closed', 'collapse')
    sortable_options = []


class FileInputSampleInline(CompactInline):
    model = FileInputSample
    form = InputSampleForm
    extra = 0
    fk_name = 'file_input'
    fields = ['label', 'file', 'file_input']
    exclude = ['order']
    classes = ('grp-collapse grp-closed', 'collapse')


class RepeatGroupAdmin(WavesModelAdmin):
    # readonly_fields = ['submission']
    # readonly_fields = ['submission']
    exclude = ['order']

    def get_model_perms(self, request):
        return {}  # super(AllParamModelAdmin, self).get_model_perms(request)


class OrgRepeatGroupInline(CompactInline):
    model = RepeatedGroup
    extra = 0
    verbose_name = "Input group"
    exclude = ['order']
    verbose_name_plural = "Input groups"
    classes = ('grp-collapse grp-closed', 'collapse')


class OrganizeInputInline(SortableInlineAdminMixin, admin.TabularInline):
    model = AParam
    form = InputInlineForm
    classes = ["collapse", ]
    fields = ['class_label', 'label', 'name', 'multiple', 'required', 'default']
    readonly_fields = ['class_label']
    ordering = ('order', '-required')
    extra = 0
    show_change_link = True

    def class_label(self, obj):
        if obj.parent:
            level = 0
            init = obj.parent
            while init:
                level += 1
                init = init.parent
            return mark_safe("<span class='icon-arrow-right'></span>" * level +
                             "%s (%s)" % (obj._meta.verbose_name, obj.when_value))
        return obj._meta.verbose_name

    def get_queryset(self, request):
        return super(OrganizeInputInline, self).get_queryset(request).order_by('-required', 'order')


class ServiceSubmissionAdmin(PolymorphicInlineSupportMixin, WavesModelAdmin, DynamicInlinesAdmin):
    """ Submission process administration -- Model Submission """
    current_obj = None
    form = ServiceSubmissionForm
    exclude = ['order']
    list_display = ['get_name', 'service', 'runner_link', 'available_online', 'available_api', 'runner']
    readonly_fields = ['available_online', 'available_api', 'get_command_line_pattern']
    list_filter = (
        'service__name',
        'availability'
    )
    search_fields = ('service__name', 'label', 'override_runner__name', 'service__runner__name')
    fieldsets = [
        ('General', {
            'fields': ['service', 'name', 'availability', 'api_name'],
            'classes': ['collapse', 'open']
        }),
        ('Run Config', {
            'fields': ['runner', 'get_command_line_pattern', 'binary_file'],
            'classes': ['collapse']
        }),
    ]
    show_full_result_count = True
    change_form_template = "admin/waves/submission/change_form.html"

    inlines = (
        OrganizeInputInline,
        # OrgRepeatGroupInline,
        SubmissionOutputInline,
        ExitCodeInline
    )

    def get_inline_instances(self, request, obj=None):
        inline_instances = [inline(self.model, self.admin_site) for inline in self.inlines]
        if obj and obj.runner is not None and obj.runner.adaptor_params.filter(prevent_override=False).count() > 0:
            inline_instances.append(SubmissionRunnerParamInLine(self.model, self.admin_site))
        return inline_instances

    def add_view(self, request, form_url='', extra_context=None):
        context = extra_context or {}
        context['show_save_as_new'] = False
        context['show_save_and_add_another'] = False
        context['show_save'] = False
        return super(ServiceSubmissionAdmin, self).add_view(request, form_url, context)

    def get_form(self, request, obj=None, **kwargs):
        request.current_obj = obj
        form = super(ServiceSubmissionAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['runner'].required = False
        return form

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(ServiceSubmissionAdmin, self).get_fieldsets(request, obj)
        if obj is None:  # i.e create mode
            elem = fieldsets[0][1]
            elem['classes'].append('open') if 'open' not in elem['classes'] else None
            elem['fields'].remove('available_api') if 'available_api' in elem['fields'] else None
            elem['fields'].remove('available_online') if 'available_online' in elem['fields'] else None
            elem['fields'].remove('api_name') if 'api_name' in elem['fields'] else None
        return fieldsets

    def get_name(self, obj):
        return mark_safe("<span title='Edit submission'>%s (%s)</span>" % (obj.name, obj.service))

    get_name.short_description = "Name"

    def get_command_line_pattern(self, obj):
        if not obj.adaptor:
            return "N/A"
        return "%s %s" % (obj.adaptor.command, obj.service.command.create_command_line(job_inputs=obj.inputs.all()))

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super(ServiceSubmissionAdmin, self).get_readonly_fields(request, obj))
        if obj is not None:
            readonly_fields.append('service')
        return readonly_fields

    def available_api(self, obj):
        return obj.available_api

    def available_online(self, obj):
        return obj.available_online

    def save_model(self, request, obj, form, change):
        if not obj.runner:
            obj.adaptor_params.all().delete()
        super(ServiceSubmissionAdmin, self).save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False

    def runner_link(self, obj):
        return obj.get_runner()

    def response_add(self, request, obj, post_url_continue=None):
        if '_continue' not in request.POST:
            messages.success(request, "Submission %s successfully saved" % obj)
            return HttpResponseRedirect(obj.service.get_admin_url() + "#/tab/inline_0/")
        else:
            return super(ServiceSubmissionAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if '_continue' not in request.POST:
            messages.success(request, "Submission %s successfully saved" % obj)
            return HttpResponseRedirect(obj.service.get_admin_url() + "#/tab/inline_0/")
        else:
            return super(ServiceSubmissionAdmin, self).response_change(request, obj)


admin.site.register(RepeatedGroup, RepeatGroupAdmin)
admin.site.register(Submission, ServiceSubmissionAdmin)
