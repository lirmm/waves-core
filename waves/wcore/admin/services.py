from __future__ import unicode_literals

import swapper
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe

from waves.wcore.admin.adaptors import ServiceRunnerParamInLine
from waves.wcore.admin.base import *
from waves.wcore.models.binaries import ServiceBinaryFile
from waves.wcore.admin.forms.services import SubmissionInlineForm, ServiceForm
from waves.wcore.models.services import Submission
from waves.wcore.utils import url_to_edit_object

Service = swapper.load_model("wcore", "Service")
User = get_user_model()

__all__ = ['ServiceAdmin', 'ServiceSubmissionInline']


class ServiceSubmissionInline(admin.TabularInline):
    """ Service Submission Inline (included in ServiceAdmin) """
    model = Submission
    form = SubmissionInlineForm
    extra = 1
    fk_name = 'service'
    sortable = 'order'
    sortable_field_name = "order"
    classes = ('grp-collapse grp-closed', 'collapse')
    fields = ['name', 'availability', 'api_name', 'get_runner']
    readonly_fields = ['api_name', 'get_runner']
    show_change_link = True

    def get_runner(self, obj):
        return obj.runner or "-"

    get_runner.short_description = "Overridden runner"


class ServiceBinaryInline(admin.TabularInline):
    model = ServiceBinaryFile


class ServiceAdmin(ExportInMassMixin, DuplicateInMassMixin, MarkPublicInMassMixin, WavesModelAdmin,
                   DynamicInlinesAdmin):
    """ Service model objects Admin"""

    class Media:
        js = ('admin/waves/js/services.js',
              'admin/waves/js/connect.js')

    form = ServiceForm
    filter_horizontal = ['restricted_client']
    readonly_fields = ['remote_service_id', 'created', 'updated', 'submission_link']
    list_display = ('name', 'api_name', 'runner', 'version', 'status', 'created_by',
                    'submission_link')
    list_filter = ('status', 'name', 'created_by')
    change_form_template = "admin/waves/service/change_form.html"

    fieldsets = [
        ('General', {
            'fields': ['name', 'created_by', 'version', 'created', 'updated', 'short_description'],
            'classes': ('grp-collapse grp-closed', 'collapse', 'open')

        }),
        ('Run Config', {
            'fields': ['runner', 'binary_file'],
            'classes': ('collapse', )
        }),
        ('Access', {
            'classes': ('grp-collapse grp-closed', 'collapse'),
            'fields': ['status', 'restricted_client', 'api_on', 'web_on', 'email_on', ]
        }),
        ('Details', {
            'classes': ('grp-collapse grp-closed', 'collapse'),
            'fields': ['api_name', 'description', 'edam_topics',
                       'edam_operations', 'remote_service_id', ]
        }),
    ]
    extra_fieldsets = None
    override_fieldsets = False

    def get_fieldsets(self, request, obj=None):
        base_fieldsets = super(ServiceAdmin, self).get_fieldsets(request, obj)
        if self.override_fieldsets:
            field_sets = self.extra_fieldsets
        elif self.extra_fieldsets is not None:
            field_sets = base_fieldsets + self.extra_fieldsets
        else:
            field_sets = base_fieldsets
        return field_sets

    inlines = (ServiceRunnerParamInLine,
               ServiceSubmissionInline)

    def get_inline_instances(self, request, obj=None):
        inline_instances = []
        if obj and obj.runner is not None and obj.runner.adaptor_params.filter(prevent_override=False).count() > 0:
            inline_instances.append(ServiceRunnerParamInLine(self.model, self.admin_site))
        inline_instances.append(ServiceSubmissionInline(self.model, self.admin_site))
        return inline_instances

    # Override admin class and set this list to add your inlines to service admin

    def add_view(self, request, form_url='', extra_context=None):
        context = extra_context or {}
        context['show_save_as_new'] = False
        context['show_save_and_add_another'] = False
        context['show_save'] = False
        return super(ServiceAdmin, self).add_view(request, form_url, context)

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
        if obj and obj.status > Service.SRV_TEST and not 'api_name' in readonly_fields:
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
        # form.base_fields['runner'].widget.can_delete_related = False
        # form.base_fields['runner'].widget.can_add_related = False
        # form.base_fields['runner'].widget.can_change_related = False
        form.base_fields['created_by'].widget.can_change_related = False
        form.base_fields['created_by'].widget.can_add_related = False
        form.base_fields['created_by'].widget.can_delete_related = False

        return form

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        """ Filter runner and created_by list """
        if db_field.name == "created_by":
            kwargs['queryset'] = User.objects.filter(is_staff=True)
        return super(ServiceAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Service, ServiceAdmin)
