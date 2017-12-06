"""
Admin pages for Runner and RunnerParam models objects
"""
from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.admin import register, TabularInline
from django.contrib.admin.options import IS_POPUP_VAR

from base import ExportInMassMixin
from waves.wcore.admin.adaptors import RunnerParamInline
from waves.wcore.admin.base import WavesModelAdmin, DynamicInlinesAdmin
from waves.wcore.admin.forms.runners import RunnerForm
from waves.wcore.models import Runner, get_service_model, get_submission_model

Service = get_service_model()
Submission = get_submission_model()

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
    fields = ['name', 'availability', 'created', 'updated']
    readonly_fields = ['name', 'availability', 'created', 'updated']
    show_change_link = True
    verbose_name_plural = "Related Submissions"

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
class RunnerAdmin(ExportInMassMixin, WavesModelAdmin):
    """ Admin for Job Runner """
    model = Runner
    form = RunnerForm
    inlines = (RunnerParamInline, ServiceRunInline)
    list_display = ('name', 'get_runner_clazz', 'connexion_string', 'short_description', 'nb_services')
    list_filter = ('name', 'clazz')
    readonly_fields = ['connexion_string']
    fieldsets = [
        ('Main', {
            'fields': ['name', 'clazz', 'connexion_string', 'binary_file', 'update_init_params']
        }),
        ('Description', {
            'fields': ['short_description', 'description'],
            'classes': ('collapse grp-collapse grp-closed',),
        }),
    ]
    change_form_template = "admin/waves/runner/change_form.html"

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
                    service.set_defaults()
                    """
                    for job in service.pending_jobs.all():
                        if job.adaptor is not None:
                            job.run_cancel()
                        message += '<br/>- Related pending job %s has been cancelled' % job.title
                    """
                    messages.info(request, message)

    def connexion_string(self, obj):
        concrete = obj.adaptor
        if concrete is not None:
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
