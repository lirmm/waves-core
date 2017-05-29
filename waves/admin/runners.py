"""
Admin pages for Runner and RunnerParam models objects
"""
from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.admin import register, TabularInline
from django.contrib.admin.options import IS_POPUP_VAR

from base import ExportInMassMixin
from waves.admin.adaptors import RunnerParamInline
from waves.admin.base import WavesModelAdmin, DynamicInlinesAdmin
from waves.admin.forms.runners import RunnerForm
from waves.models import Runner, Service, Submission

__all__ = ['RunnerAdmin']


class ServiceRunInline(TabularInline):
    """ List of related services """
    model = Service
    extra = 0
    fields = ['name', 'version', 'created', 'updated', 'created_by']
    readonly_fields = ['name', 'version', 'created', 'updated', 'created_by']
    show_change_link = True
    verbose_name_plural = "Running Services"

    def has_delete_permission(self, request, obj=None):
        """ No delete permission for runners params
        :return: False
        """
        return False

    def has_add_permission(self, request):
        """ No add permission for runners params
        :return: False
        """
        return False


class SubmissionRunInline(TabularInline):
    """ List of related services """
    model = Submission
    extra = 0
    fields = ['name', 'availability', 'created', 'updated', 'service', ]
    readonly_fields = ['label', 'availability', 'created', 'updated', 'service', ]
    show_change_link = True
    verbose_name_plural = "Running Submissions"

    def has_delete_permission(self, request, obj=None):
        """ No delete permission for runners params
        :return: False
        """
        return False

    def has_add_permission(self, request):
        """ No add permission for runners params
        :return: False
        """
        return False


@register(Runner)
class RunnerAdmin(ExportInMassMixin, WavesModelAdmin, DynamicInlinesAdmin):
    """ Admin for Job Runner """
    model = Runner
    form = RunnerForm
    # inlines = (RunnerParamInline, ServiceRunInline)
    list_display = ('name', 'get_runner_clazz', 'connexion_string', 'short_description', 'nb_services')
    list_filter = ('name', 'clazz')
    readonly_fields = ['connexion_string']
    fieldsets = [
        ('Main', {
            'fields': ['name', 'clazz', 'connexion_string', 'update_init_params']
        }),
        ('Description', {
            'fields': ['short_description', 'description'],
            'classes': ('collapse grp-collapse grp-closed',),
        }),
    ]

    def get_inlines(self, request, obj=None):
        _inlines = [
            RunnerParamInline,
        ]
        if obj and IS_POPUP_VAR not in request.GET:
            self.inlines = _inlines
            if obj.waves_submission_runs.count() > 0:
                self.inlines.append(SubmissionRunInline)
            if obj.waves_service_runs.count() > 0:
                self.inlines.append(ServiceRunInline)
        elif IS_POPUP_VAR not in request.GET:
            self.inlines = [_inlines[0], ]
        return self.inlines

    def add_view(self, request, form_url='', extra_context=None):
        context = extra_context or {}
        context['show_save_as_new'] = IS_POPUP_VAR in request.GET
        context['show_save_and_add_another'] = False
        context['show_save'] = IS_POPUP_VAR in request.GET
        return super(RunnerAdmin, self).add_view(request, form_url, context)

    def nb_services(self, obj):
        return len(obj.runs)

    nb_services.short_description = "Running Services"

    def save_model(self, request, obj, form, change):
        """ Add related Service / Jobs updates upon Runner modification """
        super(RunnerAdmin, self).save_model(request, obj, form, change)
        if obj is not None:
            if 'update_init_params' in form.changed_data:
                for service in obj.runs:
                    message = 'Related %s has been reset' % service
                    service.set_run_params_defaults()
                    # TODO sometime we should save runParams directly in jobs, so won't rely on db modification
                    for job in service.pending_jobs.all():
                        job.adaptor.cancel_job(job=job)
                        message += '<br/>- Related pending job %s has been cancelled' % job.title
                    messages.info(request, message)

    def connexion_string(self, obj):
        concrete = obj.adaptor
        if concrete:
            return obj.adaptor.connexion_string()
        else:
            return 'n/a'

    connexion_string.short_description = 'Connexion String'

    def get_runner_clazz(self, obj):
        concrete = obj.adaptor
        if concrete:
            return obj.clazz
        else:
            return "Implementation class not available !"


