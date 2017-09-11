from __future__ import unicode_literals

from waves.wcore.compat import SortableInlineAdminMixin
from django.contrib import admin
from django.utils.safestring import mark_safe

from waves.wcore.admin.forms.services import InputInlineForm
from waves.wcore.models import AParam


class OrganizeInputInline(SortableInlineAdminMixin, admin.TabularInline):
    model = AParam
    form = InputInlineForm
    fields = ['label', 'class_label', 'name', 'required', 'cmd_format', 'default', 'step', 'order']
    readonly_fields = ['class_label', 'step', 'aparam_ptr']
    classes = ('grp-collapse', 'grp-closed', 'collapse', 'show-change-link-popup')
    can_delete = True
    extra = 0
    show_change_link = True
    list_per_page = 5

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

    class_label.short_description = "Input type"

    def get_queryset(self, request):
        return super(OrganizeInputInline, self).get_queryset(request).order_by('-required', 'order')

    def step(self, obj):
        if hasattr(obj, 'step'):
            return obj.step
        else:
            return 'N/A'
