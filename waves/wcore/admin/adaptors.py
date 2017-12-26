# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.contenttypes.admin import GenericTabularInline

from waves.wcore.admin.forms.adaptors import AdaptorInitParamForm
from waves.wcore.models import AdaptorInitParam


class AdaptorInitParamInline(GenericTabularInline):
    form = AdaptorInitParamForm
    model = AdaptorInitParam
    extra = 0
    max_num = 0
    fields = ['name', 'value', 'default_value', 'prevent_override']
    readonly_fields = ('name', 'default_value')
    classes = ('collapse grp-collapse grp-closed',)
    suit_classes = 'suit-tab suit-tab-adaptor'
    can_delete = False
    verbose_name = 'Execution param'
    verbose_name_plural = "Execution parameters"

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

    def default_value(self, obj):
        """ Get default values from related adaptor concrete class instance """
        init_value = getattr(obj.content_object, 'crypt')
        if init_value is not None:
            return "*" * len(init_value) if init_value is not None else '-'
        if hasattr(init_value, '__iter__'):
            return 'list'
        return init_value if init_value is not None else '-'


class RunnerParamInline(AdaptorInitParamInline):
    """ Job Runner class instantiation parameters insertion field
    Inline are automatically generated from effective implementation class 'init_params' property """
    model = AdaptorInitParam


class ServiceRunnerParamInLine(AdaptorInitParamInline):
    """ Adaptors parameters for Service """
    model = AdaptorInitParam

    def get_queryset(self, request):
        queryset = super(ServiceRunnerParamInLine, self).get_queryset(request)
        queryset = queryset.filter(prevent_override=False)
        return queryset

    def has_add_permission(self, request):
        return False


class SubmissionRunnerParamInLine(AdaptorInitParamInline):
    """ Adaptors parameters for submission when overridden """
    model = AdaptorInitParam
    fields = ['name', 'value', ]

    def get_queryset(self, request):
        queryset = super(SubmissionRunnerParamInLine, self).get_queryset(request)
        queryset = queryset.filter(prevent_override=False)
        return queryset
