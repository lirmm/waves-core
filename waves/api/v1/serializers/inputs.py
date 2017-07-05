from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework.fields import empty

from waves.models.inputs import *
from waves.api.share import DynamicFieldsModelSerializer, RecursiveField
from .fields import ListElementField


class AParamSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['label', 'name', 'default', 'format', 'type', 'mandatory', 'short_description', 'multiple',
                  'when']
        model = AParam

    mandatory = serializers.NullBooleanField(source='required')
    short_description = serializers.CharField(source='help_text')
    type = serializers.SerializerMethodField(source='param_type')
    when = RecursiveField(many=True, read_only=True, source='dependents_inputs')

    @staticmethod
    def get_type(param):
        if param.type == AParam.TYPE_LIST:
            return "select"
        elif param.type == AParam.TYPE_DECIMAL:
            return "float"
        elif param.type == AParam.TYPE_INT:
            return "number"
        return param.type

    def to_representation(self, instance):
        repr_initial = super(AParamSerializer, self).to_representation(instance)
        if instance.dependents_inputs.count() == 0:
            repr_initial.pop('dependents_inputs', None)
            repr_initial.pop('when', None)
        if instance.when_value is not None:
            reprs = {instance.when_value: repr_initial}
            return reprs

        return repr_initial


class TextParamSerializer(AParamSerializer):
    class Meta(AParamSerializer.Meta):
        model = TextParam
        fields = AParamSerializer.Meta.fields + ['max_length']

    max_length = serializers.IntegerField()


class IntegerSerializer(AParamSerializer):
    class Meta(AParamSerializer.Meta):
        model = IntegerParam
        fields = AParamSerializer.Meta.fields

    default = serializers.IntegerField()


class BooleanSerializer(AParamSerializer):
    class Meta(AParamSerializer.Meta):
        model = BooleanParam
        fields = AParamSerializer.Meta.fields


class DecimalSerializer(AParamSerializer):
    class Meta:
        model = DecimalParam
        fields = AParamSerializer.Meta.fields

    default = serializers.DecimalField(decimal_places=3, max_digits=50, coerce_to_string=False)


class FileSerializer(AParamSerializer):
    class Meta(AParamSerializer.Meta):
        model = FileInput
        fields = AParamSerializer.Meta.fields

    format = serializers.CharField(source='allowed_extensions')


class ListSerialzer(AParamSerializer):
    class Meta(AParamSerializer.Meta):
        model = ListParam
        fields = AParamSerializer.Meta.fields + ['format']

    format = ListElementField(source='list_elements')


class InputSerializer(DynamicFieldsModelSerializer):
    """ Serialize JobInput """

    class Meta:
        model = AParam
        queryset = AParam.objects.all()
        fields = ('label', 'name', 'default', 'param_type', 'mandatory', 'description', 'multiple')
        extra_kwargs = {
            'url': {'view_name': 'waves:api_v2:waves-services-detail', 'lookup_field': 'api_name'}
        }

    description = serializers.CharField(source='help_text')

    def __init__(self, instance=None, data=empty, **kwargs):
        super(InputSerializer, self).__init__(instance, data, **kwargs)

    def to_representation(self, obj):
        """ Return representation for an Input, including dependents inputs if needed """
        if isinstance(obj, FileInput):
            return FileSerializer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, ListParam):
            return ListSerialzer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, BooleanParam):
            return BooleanSerializer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, DecimalParam):
            return DecimalSerializer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, IntegerParam):
            return IntegerSerializer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, TextParam):
            return TextParamSerializer(obj, context=self.context).to_representation(obj)
        else:
            return AParamSerializer(obj, context=self.context).to_representation(obj)


class RelatedInputSerializer(InputSerializer):
    """ Serialize a dependent Input (RelatedParam models) """

    class Meta:
        fields = InputSerializer.Meta.fields

    def to_representation(self, instance):
        """ Return representation of a Related Input """
        initial_repr = super(RelatedInputSerializer, self).to_representation(instance)
        return {instance.when_value: initial_repr}


class ConditionalInputSerializer(DynamicFieldsModelSerializer):
    """ Serialize inputs if it's a conditional one """

    class Meta:
        model = AParam
        fields = (
            'label', 'name', 'default', 'param_type', 'cmd_format', 'mandatory', 'description', 'multiple', 'when')

    when = RelatedInputSerializer(source='dependents_inputs', many=True, read_only=True)
    description = serializers.CharField(source='help_text')
    param_type = serializers.SerializerMethodField(source='param_type')

    @staticmethod
    def get_param_type(param):
        if param.type == AParam.TYPE_LIST:
            return "select"
        elif param.type == AParam.TYPE_DECIMAL:
            return "float"
        elif param.type == AParam.TYPE_INT:
            return "number"
        return param.type
