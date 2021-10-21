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
from django.contrib import messages
from django.contrib.admin import register, TabularInline
from django.contrib.admin.options import IS_POPUP_VAR

from waves.models import Runner, Service, Submission
from .adaptors import RunnerParamInline
from .base import ExportInMassMixin, WavesModelAdmin
from .forms import RunnerForm
from .views import RunnerExportView, RunnerImportToolView, RunnerTestConnectionView


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

    def has_add_permission(self, request, obj):
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

    def has_add_permission(self, request, obj):
        return False


@register(Runner)
class RunnerAdmin(ExportInMassMixin, WavesModelAdmin):
    """ Admin for Job Runner """

    # noinspection PyClassHasNoInit
    class Media:
        """ Medias """
        js = ('waves/admin/js/runner.js',
              'waves/admin/js/connect.js')

    model = Runner
    # form = RunnerForm
    inlines = (RunnerParamInline, ServiceRunInline)
    list_display = ('name', 'runner_clazz', 'short_description', 'connexion_string', 'enabled', 'nb_services', 'id')
    list_filter = ('name', 'clazz')
    list_display_links = ('name',)
    readonly_fields = ['connexion_string']
    fieldsets = [
        ('Main', {
            #'fields': ['name', 'clazz', 'connexion_string', 'enabled', 'update_init_params']
            'fields': ['name', 'clazz', 'connexion_string', 'enabled']#, 'update_init_params']
        }),
        ('Extended Description', {
            'fields': ['short_description', 'description'],
            'classes': ('collapse grp-collapse',),
        }),
    ]
    change_form_template = "waves/admin/runner/change_form.html"

    def get_urls(self):
        urls = super(RunnerAdmin, self).get_urls()
        extended_urls = [
            url(r'^(?P<pk>\d+)/import$', RunnerImportToolView.as_view(), name="runner_import_form"),
            url(r'^(?P<pk>\d+)/export$', RunnerExportView.as_view(), name="runner_export_form"),
            url(r'^(?P<pk>\d+)/check$', RunnerTestConnectionView.as_view(), name="runner_test_connection"),
        ]
        return urls + extended_urls

    def add_view(self, request, form_url='', extra_context=None):
        context = extra_context or {}
        context['show_save_as_new'] = IS_POPUP_VAR in request.GET
        context['show_save'] = False  # IS_POPUP_VAR in request.GET
        # TODO check if really needed for in pop_up context
        context['show_save_and_continue'] = IS_POPUP_VAR not in request.GET
        return super(RunnerAdmin, self).add_view(request, form_url, context)

    def nb_services(self, obj):
        return len(obj.runs())

    def get_fieldsets(self, request, obj=None):
        if obj is None or obj.adaptor is None:
            return [
                ('Main', {
                    #'fields': ['name', 'clazz', 'connexion_string', 'update_init_params']
                    'fields': ['name', 'clazz', 'connexion_string', 'enabled']#, 'update_init_params']
                })
            ]
        else:
            return self.fieldsets

    def get_inlines(self, request, obj):
        if obj is None or obj.adaptor is None:
            return ()
        return super(RunnerAdmin, self).get_inlines(request, obj)

    def runner_clazz(self, obj):
        return obj.adaptor.name if obj.adaptor else "Implementation class not available !"

    def save_model(self, request, obj, form, change):
        super(RunnerAdmin, self).save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if form.changed_data:
            if 'clazz' in form.changed_data:
                # Reset current runner adaptor initial params since underlying class changed
                form.instance.set_defaults()
            if 'enabled' in form.changed_data and form.cleaned_data['enabled'] is False:
                # Disable related services if runner has been disabled
                for running in form.instance.running_services():
                    running.status = Service.SRV_DRAFT
                    running.save(update_fields=['status'])
        # Force save current object for subsequents request
        for form_set in formsets:
            if form_set.has_changed():
                form.instance.save()
                # Reset Services / Submission configs if Runner configuration has changed
                for running in form.instance.runs():
                    message = '%s has been updated/deactivated' % running
                    running.set_defaults()
                    messages.info(request, message)

    def connexion_string(self, obj):
        return obj.adaptor.connexion_string() if obj and obj.adaptor is not None else 'N/A'

    nb_services.short_description = "Related Services"
    runner_clazz.short_description = "Type"
    connexion_string.short_description = 'Connexion string'
