from __future__ import unicode_literals

from django.contrib.auth import get_user_model

from base import ExportInMassMixin, DuplicateInMassMixin, MarkPublicInMassMixin
from waves.admin.adaptors import ServiceRunnerParamInLine
from waves.admin.submissions import *
from waves.models.services import *
from waves.models.submissions import *
from waves.utils import url_to_edit_object

User = get_user_model()

__all__ = ['ServiceAdmin']


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


@admin.register(Service)
class ServiceAdmin(ExportInMassMixin, DuplicateInMassMixin, MarkPublicInMassMixin, WavesModelAdmin,
                   DynamicInlinesAdmin):
    """ Service model objects Admin"""

    class Media:
        js = ('waves/admin/js/services.js',
              'waves/admin/js/connect.js')

    form = ServiceForm
    filter_horizontal = ['restricted_client']
    readonly_fields = ['remote_service_id', 'created', 'updated', 'submission_link']
    list_display = ('name', 'api_name', 'runner', 'version', 'status', 'created_by',
                    'submission_link')
    list_filter = ('status', 'name', 'created_by')

    fieldsets = (
        ('General', {
            'classes': ('grp-collapse grp-closed', 'collapse'),
            'fields': ['name', 'created_by', 'runner', 'version', 'created', 'updated', ]
        }),
        ('Access', {
            'classes': ('grp-collapse grp-closed', 'collapse'),
            'fields': ['status', 'restricted_client', 'api_on', 'web_on', 'email_on', ]
        }),
        ('Details', {
            'classes': ('grp-collapse grp-closed', 'collapse'),
            'fields': ['api_name', 'short_description', 'description', 'edam_topics',
                       'edam_operations', 'remote_service_id', ]
        }),
    )

    # Override admin class and set this list to add your inlines to service admin
    def get_inlines(self, request, obj=None):
        _inlines = []
        self.inlines = _inlines
        if obj:
            self.inlines.append(ServiceSubmissionInline)
            if obj.runner is not None and obj.runner.adaptor_params.filter(prevent_override=False).count() > 0:
                self.inlines.append(ServiceRunnerParamInLine)
        return self.inlines

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
        if obj and obj.status > Service.SRV_TEST:
            readonly_fields.append('api_name')
        else:
            readonly_fields.remove('api_name') if 'api_name' in readonly_fields else None
        if obj is not None and obj.created_by != request.user:
            readonly_fields.append('clazz')
            readonly_fields.append('version')
        return readonly_fields

    def get_form(self, request, obj=None, **kwargs):
        """ Assign current obj to form """
        request.current_obj = obj
        form = super(ServiceAdmin, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        form.base_fields['runner'].widget.can_delete_related = False
        form.base_fields['runner'].widget.can_add_related = False
        form.base_fields['runner'].widget.can_change_related = False
        form.base_fields['created_by'].widget.can_change_related = False
        form.base_fields['created_by'].widget.can_add_related = False
        form.base_fields['created_by'].widget.can_delete_related = False

        return form

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        """ Filter runner and created_by list """
        if db_field.name == "created_by":
            kwargs['queryset'] = User.objects.filter(is_staff=True)
        return super(ServiceAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


