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

from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin import TabularInline
from django.utils.safestring import mark_safe

from waves.core.const import JobStatus
from waves.core.utils import url_to_edit_object
from waves.models import JobHistory, JobInput, Job, JobOutput
from .base import WavesModelAdmin
from .forms import JobInputForm, JobOutputForm, JobForm
from .views import JobCancelView, JobRerunView

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
    readonly_fields = ('name', 'api_name', 'value', 'file_path')
    ordering = ('order',)
    fields = ('name', 'api_name', 'value', 'file_path')

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
            except Exception as e:
                messages.error(request, message="Job [%s] error %s " % (job.title, e))
        else:
            messages.warning(request, 'Job [%s] ignored because its status is already created' % job.title)


def delete_model(modeladmin, request, queryset):
    for obj in queryset.all():
        if obj.client == request.user or request.user.is_superuser:
            try:
                obj.delete()
                messages.success(request, message="Jobs %s successfully deleted" % obj)
            except Exception as e:
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
    ]
    actions = [mark_rerun, delete_model]
    list_filter = ('_status', 'client')
    list_display = ('get_slug', 'title', 'get_colored_status', 'submission_service_name', 'get_run_on', 'get_client',
                    'created', 'updated')
    list_per_page = 30
    search_fields = ('client__email', 'get_run_on')
    readonly_fields = ('title', 'slug', 'submission_service_name', 'email_to', '_status', 'created', 'updated',
                       'get_run_on', 'command_line_arguments', 'remote_job_id', 'submission_name', 'nb_retry',
                       'connexion_string', 'get_command_line', 'working_dir', 'exit_code', 'get_run_details')

    fieldsets = [
        ('Main', {'classes': ('', 'suit-tab', 'suit-tab-general',),
                  'fields': ['title', 'slug', 'email_to', '_status', 'created', 'updated',
                             'client', 'exit_code', 'get_run_details']
                  }
         ),
        ('Submission', {
            'classes': ('collapse', 'suit-tab', 'suit-tab-general',),
            'fields': ['remote_job_id', 'submission_name', 'get_run_on', 'working_dir', 'connexion_string',
                       'get_command_line', 'nb_retry']
        }
         )
    ]

    def get_urls(self):
        urls = super(JobAdmin, self).get_urls()
        extended_urls = [
            url(r'^job/(?P<job_id>[0-9]+)/cancel/$', JobCancelView.as_view(), name='job_cancel'),
            url(r'^job/(?P<job_id>[0-9]+)/rerun/$', JobRerunView.as_view(), name='job_rerun'),
        ]
        return urls + extended_urls

    def get_run_details(self, obj):
        return "N/A" if obj.run_details is None else mark_safe("<pre>" + "".join(
            ['\n{}: {}'.format(det[0], det[1]) for det in vars(obj.run_details).items()]) + "</pre>")

    def submission_name(self, obj):
        return url_to_edit_object(obj.submission)

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

    def get_list_filter(self, request):
        return super(JobAdmin, self).get_list_filter(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or (
                obj is not None and (obj.client == request.user or obj.submission.service.created_by == request.user))

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
            JobStatus.JOB_COMPLETED: 'success',
            JobStatus.JOB_RUNNING: 'warning',
            JobStatus.JOB_ERROR: 'error',
            JobStatus.JOB_CANCELLED: 'error',
            JobStatus.JOB_PREPARED: 'info',
            JobStatus.JOB_CREATED: 'info',
        }.get(obj.status)
        if css_class:
            return {'class': css_class}

    def get_form(self, request, obj=None, **kwargs):
        request.current_obj = obj
        form = super(JobAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['client'].widget.can_add_related = False
        return form

    def get_run_on(self, obj):
        if obj.submission is not None and obj.submission.get_runner():
            return url_to_edit_object(obj.submission.get_runner())
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

    def get_command_line(self, job):
        if job.adaptor:
            return "%s %s" % (job.adaptor.command, job.command_line_arguments)
        else:
            return "Unavailable"

    def submission_service_name(self, obj):
        if obj.submission:
            return "%s [%s]" % (obj.submission.service.name, obj.submission.name)
        else:
            return "Unavailable"

    connexion_string.short_description = "Remote connexion string"
    submission_service_name.short_description = "Service [submission]"
    get_command_line.short_description = "Remote command line"
    get_colored_status.short_description = 'Status'
    get_run_on.short_description = 'Run on'
    get_client.short_description = 'Email'
    get_slug.short_description = 'Identifier'
    get_slug.admin_order_field = 'slug'
    get_colored_status.admin_order_field = 'status'
    get_run_on.admin_order_field = 'service__runner'
    get_client.admin_order_field = 'client'


admin.site.register(Job, JobAdmin)
