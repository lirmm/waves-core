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
from rest_framework import serializers
from rest_framework.fields import empty

from waves.api.share import DynamicFieldsModelSerializer, RecursiveField
from waves.models import AParam, TextParam, ListParam, BooleanParam, IntegerParam, FileInput, DecimalParam
from .fields import CommaSeparatedListField, ListElementField


class AParamSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['when_value', 'label', 'default', 'type', 'mandatory', 'description', 'multiple',
                  'edam_formats', 'edam_datas', 'dependents_inputs']
        model = AParam

    mandatory = serializers.NullBooleanField(source='required')
    description = serializers.CharField(source='help_text')
    edam_formats = CommaSeparatedListField()
    edam_datas = CommaSeparatedListField()
    dependents_inputs = RecursiveField(many=True, read_only=True)

    def to_representation(self, instance):
        repr_initial = super(AParamSerializer, self).to_representation(instance)
        if instance.dependents_inputs.count() == 0:
            repr_initial.pop('dependents_inputs')
        else:
            repr_initial['dependents_inputs'] = {}
            for dep_input in instance.dependents_inputs.all():
                serializer = InputSerializer(dep_input)
                repr_initial['dependents_inputs'].update({dep_input.api_name: serializer.to_representation(dep_input)})
        if instance.when_value is None:
            repr_initial.pop('when_value')
        return repr_initial

    @staticmethod
    def get_type(param):
        return param.type


class TextParamSerializer(AParamSerializer):
    class Meta(AParamSerializer.Meta):
        model = TextParam
        fields = AParamSerializer.Meta.fields + ['max_length']

    max_length = serializers.IntegerField()


class IntegerSerializer(AParamSerializer):
    class Meta(AParamSerializer.Meta):
        model = IntegerParam
        fields = AParamSerializer.Meta.fields + ['min_val', 'max_val']

    default = serializers.IntegerField()
    min_val = serializers.IntegerField()
    max_val = serializers.IntegerField()


class BooleanSerializer(AParamSerializer):
    class Meta(AParamSerializer.Meta):
        model = BooleanParam
        fields = AParamSerializer.Meta.fields + ['true_value', 'false_value']


class DecimalSerializer(AParamSerializer):
    class Meta:
        model = DecimalParam
        fields = AParamSerializer.Meta.fields + ['min_val', 'max_val']

    default = serializers.DecimalField(decimal_places=3, max_digits=50, coerce_to_string=False)
    min_val = serializers.DecimalField(decimal_places=3, max_digits=50, coerce_to_string=False)
    max_val = serializers.DecimalField(decimal_places=3, max_digits=50, coerce_to_string=False)


class FileSerializer(AParamSerializer):
    class Meta(AParamSerializer.Meta):
        model = FileInput
        fields = AParamSerializer.Meta.fields + ['max_size', 'allowed_extensions']


class ListSerializer(AParamSerializer):
    class Meta(AParamSerializer.Meta):
        model = ListParam
        fields = AParamSerializer.Meta.fields + ['values_list']

    values_list = ListElementField(source='list_elements')

class InputSerializer(DynamicFieldsModelSerializer):
    """ Serialize JobInput """

    class Meta:
        model = AParam
        queryset = AParam.objects.all()
        fields = ('label', 'name', 'default', 'type', 'mandatory', 'help_text', 'multiple', 'dependents_inputs',)
        extra_kwargs = {
            'url': {'view_name': 'wapi:v2:waves-services-detail', 'lookup_field': 'api_name'}
        }

    def __init__(self, instance=None, data=empty, **kwargs):
        super(InputSerializer, self).__init__(instance, data, **kwargs)

    def to_representation(self, obj):
        """ Return representation for an Input, including dependents inputs if needed """
        if isinstance(obj, FileInput):
            return FileSerializer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, ListParam):
            return ListSerializer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, BooleanParam):
            return BooleanSerializer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, IntegerParam):
            return IntegerSerializer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, DecimalParam):
            return DecimalSerializer(obj, context=self.context).to_representation(obj)
        elif isinstance(obj, TextParam):
            return TextParamSerializer(obj, context=self.context).to_representation(obj)
        else:
            raise Exception('Type not recognized')


class RelatedInputSerializer(InputSerializer):
    """ Serialize a dependent Input (RelatedParam models) """

    class Meta:
        fields = InputSerializer.Meta.fields

    def to_representation(self, instance):
        """ Return representation of a Related Input """
        initial_repr = super(RelatedInputSerializer, self).to_representation(instance)
        return {instance.when_value: initial_repr}


class ConditionalInputSerializer(InputSerializer):
    """ Serialize inputs if it's a conditional one """

    class Meta:
        model = AParam
        fields = ('label', 'name', 'default', 'param_type', 'cmd_format', 'mandatory', 'help_text', 'multiple',
                  'when')

    when = RelatedInputSerializer(source='dependents_inputs', many=True, read_only=True)
