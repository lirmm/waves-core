""" Base class for WAVES models.Admin """
from __future__ import unicode_literals

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

__all__ = ['DuplicateInMassMixin', 'ExportInMassMixin', 'MarkPublicInMassMixin', 'WavesModelAdmin',
           'DynamicInlinesAdmin']


def duplicate_in_mass(modeladmin, request, queryset):
    """ Duplicate selected objects """
    from django.contrib import messages
    for obj in queryset.all():
        try:
            new = obj.duplicate()
            messages.add_message(request, level=messages.SUCCESS, message="Object %s successfully duplicated" % obj)
            if queryset.count() == 1:
                return redirect(
                    reverse('admin:%s_%s_change' % (new._meta.app_label, new._meta.model_name), args=[new.id]))
        except StandardError as e:
            messages.add_message(request, level=messages.ERROR, message="Object %s error %s " % (obj, e.message))


def export_in_mass(modeladmin, request, queryset):
    """ Allow multiple models objects (inheriting from ExportAbleMixin) to be exported
     at the same time """
    for obj in queryset.all():
        try:
            file_path = obj.serialize()
            messages.add_message(request, level=messages.SUCCESS,
                                 message="Object exported successfully to %s " % file_path)
        except StandardError as e:
            messages.add_message(request, level=messages.ERROR, message="Object export %s error %s " % (obj, e.message))


def mark_public_in_mass(modeladmin, request, queryset):
    """ Allow status 'public' to be set in mass for objects implementing 'publish' method """
    for obj in queryset.all():
        try:
            obj.activate_deactivate()
            messages.add_message(request, level=messages.SUCCESS, message="Object %s successfully published" % obj)
        except StandardError as e:
            messages.add_message(request, level=messages.ERROR, message="Object %s error %s " % (obj, e.message))


class ExportInMassMixin(admin.ModelAdmin):
    """ modelAdmin mixin, add to actions 'export_in_mass' to export models to disk """

    def get_actions(self, request):
        """ Add action 'export_in_mass' """
        actions = super(ExportInMassMixin, self).get_actions(request)
        actions['export_in_mass'] = (export_in_mass, 'export_in_mass', "Export selected to disk")
        return actions


class DuplicateInMassMixin(admin.ModelAdmin):
    """ modelAdmin mixin, add to actions 'duplicate_in_mass' to export models to disk """

    def get_actions(self, request):
        """ Add action 'duplicate_in_mass' """
        actions = super(DuplicateInMassMixin, self).get_actions(request)
        actions['duplicate_in_mass'] = (duplicate_in_mass, 'duplicate_in_mass', "Duplicate selected")
        return actions


class MarkPublicInMassMixin(admin.ModelAdmin):
    """ modelAdmin mixin, add to actions 'duplicate_in_mass' to export models to disk """

    def get_actions(self, request):
        """ Add action 'duplicate_in_mass' """
        actions = super(MarkPublicInMassMixin, self).get_actions(request)
        actions['mark_public_in_mass'] = (mark_public_in_mass, 'mark_public_in_mass', "Publish/Un-publish selected")
        return actions


class WavesModelAdmin(ModelAdmin):
    """ Base models admin including global medias """

    class Media:
        js = (
            'admin/waves/js/admin.js',
            'admin/waves/js/modal.js'
        )
        css = {
            'screen': ('admin/waves/css/admin.css',
                       'admin/waves/css/modal.css')
        }


class DynamicInlinesAdmin(ModelAdmin):
    """ ModelAdmin class with dynamic inlines setup in form """

    def get_inlines(self, request, obj=None):
        """ By default returns standards inline definition """
        return self.inlines

    def get_form(self, request, obj=None, **kwargs):
        """ Set up inlines before get form """
        self.inlines = self.get_inlines(request, obj)
        return super(DynamicInlinesAdmin, self).get_form(request, obj, **kwargs)
