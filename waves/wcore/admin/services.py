from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe

from waves.wcore.compat import SortableInlineAdminMixin
from waves.wcore.admin.adaptors import ServiceRunnerParamInLine
from waves.wcore.admin.base import WavesModelAdmin, ExportInMassMixin, DuplicateInMassMixin, MarkPublicInMassMixin, \
    DynamicInlinesAdmin
from waves.wcore.admin.forms.services import SubmissionInlineForm, ServiceForm
from waves.wcore.admin.views import ServiceParamImportView, ServiceDuplicateView, ServiceExportView, \
    ServiceModalPreview, ServiceTestConnectionView
from waves.wcore.models import get_service_model, get_submission_model
from waves.wcore.models.binaries import ServiceBinaryFile
from waves.wcore.utils import url_to_edit_object

Service = get_service_model()
Submission = get_submission_model()
User = get_user_model()

__all__ = ['ServiceAdmin', 'ServiceSubmissionInline']


class ServiceSubmissionInline(SortableInlineAdminMixin, admin.TabularInline):
    """ Service Submission Inline (included in ServiceAdmin) """
    model = Submission
    form = SubmissionInlineForm
    extra = 0
    fk_name = 'service'
    sortable = 'order'
    sortable_field_name = "order"
    classes = ('grp-collapse grp-closed', 'collapse')
    fields = ['name', 'availability', 'api_name', 'runner']
    show_change_link = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return super(ServiceSubmissionInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ServiceBinaryInline(admin.TabularInline):
    model = ServiceBinaryFile


class ServiceAdmin(ExportInMassMixin, DuplicateInMassMixin, MarkPublicInMassMixin, WavesModelAdmin,
                   DynamicInlinesAdmin):
    """ Service model objects Admin"""

    class Media:
        js = ('waves/admin/js/services.js',
              'waves/admin/js/connect.js')

    form = ServiceForm

    filter_horizontal = ['restricted_client']
    readonly_fields = ['remote_service_id', 'created', 'updated', 'submission_link', 'display_run_params']
    list_display = ('id', 'get_api_name', 'name', 'status', 'get_runner', 'version', 'created_by', 'updated',
                    'submission_link')
    list_filter = ('status', 'name', 'created_by', 'runner')
    list_editable = ('status', 'name')
    list_display_links = ('get_api_name', 'id')
    ordering = ('name', 'updated')
    change_form_template = "waves/admin/service/change_form.html"

    fieldsets = [
        ('General', {
            'fields': ['name', 'created_by', 'status', 'version', 'api_name', 'short_description'],
            'classes': ('grp-collapse grp-closed', 'collapse', 'open')

        }),
        ('Computing infrastructure', {
            'fields': ['runner', 'binary_file', 'display_run_params'],
            'classes': ['collapse', ]
        }),
        ('Manage Access', {
            'classes': ('grp-collapse grp-closed', 'collapse'),
            'fields': ['email_on', 'restricted_client', ]
        }),
        ('Details', {
            'classes': ('grp-collapse grp-closed', 'collapse'),
            'fields': ['created', 'updated', 'description', 'edam_topics',
                       'edam_operations', 'remote_service_id', 'api_url']
        }),
    ]

    extra_fieldsets = []

    def get_runner(self, obj):
        return obj.runner

    get_runner.short_description = "Default execution config."

    def get_urls(self):
        urls = super(ServiceAdmin, self).get_urls()
        extended_urls = [
            url(r'^service/(?P<pk>\d+)/import/$', ServiceParamImportView.as_view(), name="service_import_form"),
            url(r'^service/(?P<service_id>\d+)/duplicate$', ServiceDuplicateView.as_view(), name="service_duplicate"),
            url(r'^service/(?P<pk>\d+)/export$', ServiceExportView.as_view(), name="service_export_form"),
            url(r'^service/(?P<pk>\d+)/check$', ServiceTestConnectionView.as_view(), name="service_test_connection"),
            url(r'^service/(?P<pk>\d+)/preview$', ServiceModalPreview.as_view(), name="service_preview"),
        ]
        return urls + extended_urls

    def get_fieldsets(self, request, obj=None):
        base_fieldsets = super(ServiceAdmin, self).get_fieldsets(request, obj)
        if obj is None:
            # create mode un-collapse RunConfig
            try:
                base_fieldsets[1][1]['classes'].remove(u'collapse')
            except ValueError:
                pass
        else:
            base_fieldsets[1][1]['classes'].append('collapse')
        return base_fieldsets + self.extra_fieldsets

    def get_inlines(self, request, obj=None):
        _inlines = [
            ServiceSubmissionInline
        ]
        if obj is not None:
            self.inlines = _inlines
        if obj and obj.get_runner() is not None \
                and obj.get_runner().adaptor_params.filter(prevent_override=False).count() > 0:
            self.inlines.insert(0, ServiceRunnerParamInLine)
        return self.inlines

    def display_run_params(self, obj):
        return ['%s:%s' % (name, value) for name, value in obj.run_params.items()]

    display_run_params.short_description = "Runner initial params"

    def add_view(self, request, form_url='', extra_context=None):
        context = extra_context or {}
        context['show_save_as_new'] = False
        context['show_save_and_add_another'] = False
        context['show_save'] = False
        return super(ServiceAdmin, self).add_view(request, form_url, extra_context=context)

    def submission_link(self, obj):
        """ Direct link to submission in list """
        links = []
        for submission in obj.submissions.all():
            links.append(url_to_edit_object(submission))
        return mark_safe("<br/>".join(links))

    submission_link.short_description = 'Submissions'

    def get_readonly_fields(self, request, obj=None):
        """ Set up readonly fields according to user profile """
        readonly_fields = super(ServiceAdmin, self).get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            readonly_fields.append('created_by')
        if obj and obj.status > Service.SRV_TEST and 'api_name' not in readonly_fields and not request.user.is_superuser:
            readonly_fields.append('api_name')
        if obj is not None and obj.created_by != request.user:
            readonly_fields.append('clazz')
            readonly_fields.append('version')
        return readonly_fields

    def get_form(self, request, obj=None, **kwargs):
        """ Assign current obj to form """
        request.current_obj = obj
        form = super(ServiceAdmin, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        try:
            form.base_fields['created_by'].widget.can_change_related = False
            form.base_fields['created_by'].widget.can_add_related = False
            form.base_fields['created_by'].widget.can_delete_related = False
        except KeyError:
            # nothing to do
            pass

        return form

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        """ Filter runner and created_by list """
        if db_field.name == "created_by":
            kwargs['queryset'] = User.objects.filter(is_staff=True)
        return super(ServiceAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Service, ServiceAdmin)
