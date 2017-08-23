from __future__ import unicode_literals

import waves.wcore.adaptors.const
from django.contrib import admin, messages
from django.contrib.admin import TabularInline
from django.db.models import Q
from waves.wcore.admin.base import WavesModelAdmin
from waves.wcore.admin.forms.jobs import JobInputForm, JobOutputForm, JobForm
from waves.wcore.models.history import JobHistory
from waves.wcore.models.jobs import *

__all__ = ['JobAdmin']


class JobInputInline(TabularInline):
    """ List JobModels inputs """
    model = JobInput
    form = JobInputForm
    extra = 0
    suit_classes = 'suit-tab suit-tab-inputs'
    exclude = ('order',)
    readonly_fields = ('name', 'api_name', 'value', 'file_path')
    can_delete = False
    ordering = ('order',)
    fields = ('name', 'api_name', 'value', 'file_path')
    classes = ['collapse', ]

    def has_add_permission(self, request):
        """ Never add any job input from admin """
        return False


class JobOutputInline(TabularInline):
    """ List job's expected outputs """
    model = JobOutput
    form = JobOutputForm
    extra = 0
    suit_classes = 'suit-tab suit-tab-outputs'
    classes = ['collapse', ]
    can_delete = False
    readonly_fields = ('name', 'value', 'file_path')
    ordering = ('order',)
    fields = ('name', 'value', 'file_path')

    def has_add_permission(self, request):
        """ Never add any job output from admin """
        return False


class JobHistoryInline(TabularInline):
    """ Job's history events """
    model = JobHistory
    verbose_name = 'Job History'
    verbose_name_plural = "Job history events"
    classes = ['collapse', ]
    readonly_fields = ('timestamp', 'status', 'get_message')
    fields = ('status', 'timestamp', 'get_message')
    can_delete = False
    extra = 0

    def has_add_permission(self, request):
        """ Never add any job output from admin """
        return False

    def get_message(self, obj):
        return obj.message.encode('utf-8')


def mark_rerun(modeladmin, request, queryset):
    """ Mark job as to be run another time """
    for job in queryset.all():
        if job.allow_rerun:
            try:
                job.re_run()
                messages.success(request, message="Job [%s] successfully marked for re-run" % job.title)
            except StandardError as e:
                messages.error(request, message="Job [%s] error %s " % (job.title, e))
        else:
            messages.warning(request, 'Job [%s] ignored because its status is already created' % job.title)


def delete_model(modeladmin, request, queryset):
    for obj in queryset.all():
        if obj.client == request.user or obj.service.created_by == request.user or request.user.is_superuser:
            try:
                obj.delete()
                messages.success(request, message="Jobs %s successfully deleted" % obj)
            except StandardError as e:
                messages.error(request, message="Job %s error %s " % (obj, e))
        else:
            messages.warning(request, message="You are not authorized to delete this job %s" % obj)


mark_rerun.short_description = "Re-run jobs"
delete_model.short_description = "Delete selected jobs"


class JobAdmin(WavesModelAdmin):
    form = JobForm
    inlines = [
        JobHistoryInline,
        JobInputInline,
        JobOutputInline,
        # TODO add jobOutputExitCode
        # TODO add JobRunDetails
    ]
    actions = [mark_rerun, delete_model]
    list_filter = ('_status', 'client')
    list_display = ('get_slug', 'get_colored_status', 'submission_service_name', 'get_run_on', 'get_client',
                    'created', 'updated')
    list_per_page = 30
    search_fields = ('client__email', 'get_run_on')
    readonly_fields = ('title', 'slug', 'submission_service_name', 'email_to', '_status', 'created', 'updated',
                       'get_run_on', 'command_line', 'remote_job_id', 'submission_name', 'nb_retry',
                       'connexion_string', 'get_command_line', 'working_dir')

    fieldsets = [
        ('Main', {'classes': ('collapse', 'suit-tab', 'suit-tab-general',),
                  'fields': ['title', 'slug', 'email_to', '_status', 'created', 'updated',
                             'client']
                  }
         ),
        ('Submission', {
            'classes': ('collapse', 'suit-tab', 'suit-tab-general',),
            'fields': ['remote_job_id', 'submission_name', 'get_run_on', 'working_dir', 'connexion_string',
                       'get_command_line', 'nb_retry']
        }
         )
    ]

    def submission_name(self, obj):
        return obj.submission.name

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_add_another'] = False
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False

        return super(JobAdmin, self).change_view(request, object_id, form_url, extra_context)

    def get_slug(self, obj):
        return str(obj.slug)

    def get_working_dir(self, obj):
        return obj.working_dir

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super(JobAdmin, self).get_queryset(request)
        else:
            qs = Job.objects.filter(
                Q(submission__service__created_by=request.user) |
                Q(client=request.user) |
                Q(email_to=request.user.email))
            ordering = self.get_ordering(request)
            if ordering:
                qs = qs.order_by(*ordering)
            return qs

    def get_list_filter(self, request):
        return super(JobAdmin, self).get_list_filter(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or (
            obj is not None and (obj.client == request.user or obj.service.created_by == request.user))

    def get_actions(self, request):
        actions = super(JobAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        has_change = super(JobAdmin, self).has_change_permission(request, obj)
        return has_change or request.user.is_superuser

    def __init__(self, model, admin_site):
        super(JobAdmin, self).__init__(model, admin_site)

    def suit_row_attributes(self, obj, request):
        css_class = {
            waves.wcore.adaptors.const.JOB_COMPLETED: 'success',
            waves.wcore.adaptors.const.JOB_RUNNING: 'warning',
            waves.wcore.adaptors.const.JOB_ERROR: 'error',
            waves.wcore.adaptors.const.JOB_CANCELLED: 'error',
            waves.wcore.adaptors.const.JOB_PREPARED: 'info',
            waves.wcore.adaptors.const.JOB_CREATED: 'info',
        }.get(obj.status)
        if css_class:
            return {'class': css_class}

    def get_form(self, request, obj=None, **kwargs):
        request.current_obj = obj
        form = super(JobAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['client'].widget.can_add_related = False
        return form

    def get_run_on(self, obj):
        if obj.submission.get_runner():
            return obj.submission.get_runner().name
        else:
            return "Undefined"

    def get_client(self, obj):
        return obj.client.email if obj.client else "Anonymous"

    def get_colored_status(self, obj):
        return obj.colored_status()

    def get_row_css(self, obj, index):
        return obj.label_class

    def get_readonly_fields(self, request, obj=None):
        read_only_fields = list(super(JobAdmin, self).get_readonly_fields(request, obj))
        return read_only_fields

    def connexion_string(self, obj):
        if obj.adaptor:
            return obj.adaptor.connexion_string()
        else:
            return "Unavailable"

    def get_command_line(self, obj):
        if obj.adaptor:
            return obj.adaptor.command + " " + obj.command_line
        else:
            return "Unavailable"

    def submission_service_name(self, obj):
        if obj.submission:
            return "%s [%s]" % (obj.submission.service.name, obj.submission.name)
        else:
            return "Unavailable"

    connexion_string.short_description = "Remote connexion string"
    get_command_line.short_description = "Remote command line"
    get_colored_status.short_description = 'Status'
    get_run_on.short_description = 'Run on'
    get_client.short_description = 'Email'
    get_slug.short_description = 'Identifier'
    get_slug.admin_order_field = 'Slug'
    get_colored_status.admin_order_field = 'status'
    get_run_on.admin_order_field = 'service__runner'
    get_client.admin_order_field = 'client'


admin.site.register(Job, JobAdmin)
