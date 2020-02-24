from django.contrib.contenttypes.admin import GenericTabularInline

from waves.core.models import AdaptorInitParam


class AdaptorInitParamInline(GenericTabularInline):
    # form = adaptors.AdaptorInitParamForm
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
        return False

    def has_add_permission(self, request, obj):
        return False

    def default_value(self, obj):
        """ Get default values from related adapter concrete class instance """
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
    verbose_name = 'Adaptor parameter'
    verbose_name_plural = "Adaptor parameters"


class ServiceRunnerParamInLine(AdaptorInitParamInline):
    """ adapters parameters for Service """
    model = AdaptorInitParam
    fields = ['name', 'value', ]

    def get_queryset(self, request):
        queryset = super(ServiceRunnerParamInLine, self).get_queryset(request)
        queryset = queryset.filter(prevent_override=False)
        return queryset


class SubmissionRunnerParamInLine(ServiceRunnerParamInLine):
    """ adapters parameters for submission when overridden """
    pass
