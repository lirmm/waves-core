""" Base class for WAVES models.Admin """
from __future__ import unicode_literals

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.core.urlresolvers import reverse
from django.db import models
from django.forms import Textarea, Select
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib.admin.templatetags.admin_modify import *
from django.contrib.admin.templatetags.admin_modify import submit_row as original_submit_row


__all__ = ['DuplicateInMassMixin', 'ExportInMassMixin', 'MarkPublicInMassMixin', 'WavesModelAdmin',
           'DynamicInlinesAdmin']


@register.inclusion_tag('waves/admin/submit_line.html', takes_context=True)
def submit_row(context):
    ctx = original_submit_row(context)
    ctx.update({
        'show_save_and_add_another': context.get('show_save_and_add_another', ctx['show_save_and_add_another']),
        'show_save_and_continue': context.get('show_save_and_continue', ctx['show_save_and_continue']),
        'show_save_as_new': context.get('show_save_as_new', ctx['show_save_as_new']),
        'show_save': context.get('show_save', ctx['show_save']),
        'show_save_and_back': context.get('show_save_and_back', ctx.get('show_save_and_back', False))
    })
    return ctx


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
            'waves/admin/js/admin.js',
            'waves/admin/js/modal.js'
        )
        css = {
            'screen': ('waves/admin/css/admin.css',
                       'waves/admin/css/modal.css')
        }

    list_per_page = 15

    @staticmethod
    def _has_group_permission(request):
        return request.user.groups.filter(name="WAVES-ADMIN").exists() or request.user.is_superuser

    def has_add_permission(self, request):
        return self._has_group_permission(request) and super(WavesModelAdmin, self).has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._has_group_permission(request) and super(WavesModelAdmin, self).has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self._has_group_permission(request) and super(WavesModelAdmin, self).has_delete_permission(request, obj)

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 3, 'cols': 50})},
        models.ForeignKey: {'widget': Select(attrs={'style': 'min-width:428px'})}
    }

    def get_api_name(self, obj):
        return obj.api_name

    get_api_name.short_description = "App short name"

    def _redirect_save_back(self, request, obj):
        return HttpResponseRedirect(request.path)

    def response_add(self, request, obj, post_url_continue=None):
        if '_saveandback' in request.POST:
            return self._redirect_save_back(request, obj)
        else:
            return super(WavesModelAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if '_saveandback' in request.POST:
            print "in response change ", request.POST.get('_saveandback')

            return self._redirect_save_back(request, obj)
        else:
            return super(WavesModelAdmin, self).response_change(request, obj)


class DynamicInlinesAdmin(ModelAdmin):
    """ ModelAdmin class with dynamic inlines setup in form """

    def get_inlines(self, request, obj=None):
        """ By default returns standards inline definition """
        return self.inlines

    def get_form(self, request, obj=None, **kwargs):
        """ Set up inlines before get form """
        self.inlines = self.get_inlines(request, obj)
        return super(DynamicInlinesAdmin, self).get_form(request, obj, **kwargs)
