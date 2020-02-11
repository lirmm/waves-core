""" Service Submission administration classes """

from django.conf import settings
from django.conf.urls import url
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from django.utils.http import urlquote
from django.utils.safestring import mark_safe

from waves.compat import CompactInline, SortableInlineAdminMixin
from waves.core.utils import url_to_edit_object
from waves.core.models import Submission, AParam, FileInputSample, FileInput, RepeatedGroup, SampleDepParam, \
    SubmissionOutput, SubmissionExitCode
from .adaptors import SubmissionRunnerParamInLine
from .base import WavesModelAdmin, DynamicInlinesAdmin
from .forms import SubmissionOutputForm, InputSampleForm, SampleDepForm2, InputInlineForm, \
    ServiceSubmissionForm, SampleDepForm
from .views import ServicePreviewForm

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
    fields = ['class_label', 'label', 'name', 'api_name', 'multiple', 'required', 'cmd_format', 'default']
    readonly_fields = ['class_label']
    ordering = ('order',)
    extra = 0
    show_change_link = True

    def get_fields(self, request, obj=None):
        if 'adminsortable2' not in settings.INSTALLED_APPS:
            fields = ['order'] + self.fields
            return fields
        return super(OrganizeInputInline, self).get_fields(request, obj)

    def class_label(self, obj):
        if obj.parent:
            level = 0
            init = obj.parent
            while init:
                level += 1
                init = init.parent
            # noinspection PyProtectedMember
            return mark_safe("<span class='icon-arrow-right'></span>" * level +
                             "%s (%s)" % (obj._meta.verbose_name, obj.when_value))
        # noinspection PyProtectedMember
        return obj._meta.verbose_name

    def get_queryset(self, request):
        return super(OrganizeInputInline, self).get_queryset(request).order_by('-required', 'order')


class ServiceSubmissionAdmin(WavesModelAdmin, DynamicInlinesAdmin):
    """ Submission process administration -- Model Submission """
    current_obj = None
    form = ServiceSubmissionForm
    exclude = ['order']
    list_display = ['name', 'api_name', 'get_service', 'availability', 'get_runner', 'updated']
    readonly_fields = ['get_command_line_pattern', 'get_run_params', 'api_url']
    list_filter = ('service__name', 'availability', 'runner')
    list_editable = ('availability',)
    list_display_links = ('name',)
    ordering = ('name', 'updated', 'created')
    search_fields = ('service__name', 'label', 'runner__name', 'service__runner__name')

    fieldsets = [
        ('General', {
            'fields': ['service', 'name', 'availability', 'api_name', 'api_url'],
            'classes': ['collapse', 'open']
        }),
        ('Run ', {
            'fields': ['runner', 'get_run_params', 'get_command_line_pattern', 'binary_file'],
            'classes': ['collapse']
        }),
    ]
    show_full_result_count = True
    change_form_template = "waves/admin/submission/change_form.html"

    def get_urls(self):
        urls = super(ServiceSubmissionAdmin, self).get_urls()
        extended_urls = [
            url(r'^submission/(?P<pk>\d+)/preview', ServicePreviewForm.as_view(), name="submission_preview"),
        ]
        return urls + extended_urls

    # Override admin class and set this list to add your inlines to service admin
    def get_run_params(self, obj):
        return obj.display_params()

    def api_url(self, obj):
        from rest_framework.reverse import reverse
        return reverse('wapi:v2:waves-services-submission-detail',
                       kwargs=dict(
                           service_app_name=obj.service.api_name,
                           submission_app_name=obj.api_name
                       ))

    api_url.short_description = "Api url"

    def get_inlines(self, request, obj=None):
        _inlines = [
            OrganizeInputInline,
            # OrgRepeatGroupInline,
            SubmissionOutputInline,
            ExitCodeInline,
        ]
        self.current_obj = obj
        self.inlines = _inlines
        if obj.runner is not None \
                and obj.get_runner().adaptor_params.filter(prevent_override=False).count() > 0:
            self.inlines.insert(0, SubmissionRunnerParamInLine)
        return self.inlines

    def add_view(self, request, form_url='', extra_context=None):
        context = extra_context or {}
        context['show_save_as_new'] = False
        context['show_save_and_add_another'] = False
        context['show_save'] = False
        return super(ServiceSubmissionAdmin, self).add_view(request, form_url, context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        context = extra_context or {}
        context['show_save_as_new'] = False
        context['show_save_and_add_another'] = False
        context['show_save_and_back'] = True
        context['show_save'] = False
        return super(ServiceSubmissionAdmin, self).change_view(request, object_id, form_url, context)

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
            elem['fields'].remove('api_name') if 'api_name' in elem['fields'] else None
        return fieldsets

    def get_name(self, obj):
        return mark_safe("<span title='Edit submission'>%s (%s)</span>" % (obj.name, obj.service))

    def get_command_line_pattern(self, obj):
        if not obj.adaptor:
            return "N/A"
        return "%s %s" % (obj.adaptor.command, obj.service.command_parser.create_command_line(inputs=obj.inputs.all()))

    def has_add_permission(self, request):
        return False

    def get_service(self, obj):
        return url_to_edit_object(obj.service)

    def get_runner(self, obj):
        return obj.get_runner().name if obj.get_runner() else 'N/A'

    def _redirect_save_back(self, request, obj):
        self.message_user(request,
                          format_html('Submission "<a href="{}">{}</a>" successfully saved', urlquote(request.path),
                                      obj), messages.SUCCESS)
        return HttpResponseRedirect(obj.service.get_admin_url() + "#/tab/inline_0/")

    def save_model(self, request, obj, form, change):
        if obj and not obj.runner:
            obj.adaptor_params.all().delete()
        super(ServiceSubmissionAdmin, self).save_model(request, obj, form, change)

    get_run_params.short_description = "Runner initial params"
    get_service.short_description = "Service"
    get_runner.short_description = "Computing infrastructure"
    get_name.short_description = "Name"
    get_command_line_pattern.short_description = "Command line pattern"

    def get_model_perms(self, request):
        # Disable direct entry to BinaryFiles
        return {}


admin.site.register(RepeatedGroup, RepeatGroupAdmin)
admin.site.register(Submission, ServiceSubmissionAdmin)
