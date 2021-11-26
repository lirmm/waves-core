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


import collections

from rest_framework import serializers
from rest_framework.reverse import reverse
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

from waves.api.share import DynamicFieldsModelSerializer
from waves.api.v2.serializers import InputSerializer as BaseInputSerializer
from waves.models import Service, Submission, SubmissionOutput

__all__ = ['OutputSerializer', 'ServiceSerializer', 'ServiceSubmissionSerializer']


@extend_schema_field(OpenApiTypes.OBJECT)
class OutputSerializer(DynamicFieldsModelSerializer):
    """ Serialize an service expected output """

    class Meta:
        model = SubmissionOutput
        fields = ('name', 'file_pattern')

    def to_representation(self, instance):
        """ Representation for a output """
        to_repr = {}
        outputs = instance.all()
        if outputs:
            for output in outputs:
                tmp_repr = [
                    ('label', output.label),
                    ('name', output.name),
                    ('file_name', output.file_pattern),
                    ('help_text', output.help_text),
                    ('edam_format', output.edam_format),
                    ('edam_data', output.edam_data),
                ]
                if hasattr(output, 'from_input') and output.from_input is not None:
                    tmp_repr.append(('issued_from', output.from_input.api_name))
                to_repr[output.api_name] = collections.OrderedDict(tmp_repr)
        return to_repr


@extend_schema_field({'type': 'object', 'additionalProperties': {'$ref': '#/components/schemas/JobInput'}, 'readOnly': True})
# extended schema to specify object return type
class InputSerializer(BaseInputSerializer):
    """ Serialize a submission input. """

    def to_representation(self, instance):
        to_repr = {}
        for baseinst in instance.all():
            base_repr = super(InputSerializer, self).to_representation(baseinst)
            to_repr[baseinst.api_name] = base_repr
        return to_repr


class ServiceSubmissionSerializer(DynamicFieldsModelSerializer,
                                  serializers.HyperlinkedRelatedField):
    """ Serialize a Service submission """

    class Meta:
        model = Submission
        fields = ('service', 'name', 'submission_app_name', 'form', 'jobs',
                  'inputs', 'outputs', 'title', 'email_to')

    view_name = 'wapi:v2:waves-services-submission-detail'

    form = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()
    jobs = serializers.SerializerMethodField()
    inputs = InputSerializer(many=False, read_only=True, source='expected_inputs')
    outputs = OutputSerializer(many=False, read_only=True)
    name = serializers.CharField(read_only=True)
    submission_app_name = serializers.CharField(read_only=True, source="api_name")
    title = serializers.CharField(write_only=True, required=False)
    email_to = serializers.CharField(write_only=True, required=False)

    def get_jobs(self, obj):
        return reverse(viewname='wapi:v2:waves-services-submission-jobs', request=self.context['request'],
                       kwargs={'service_app_name': obj.service.api_name, 'submission_app_name': obj.api_name})

    def get_form(self, obj):
        """ Return Service form endpoint uri"""
        return reverse(viewname='wapi:v2:waves-services-submission-form', request=self.context['request'],
                       kwargs={'service_app_name': obj.service.api_name, 'submission_app_name': obj.api_name})

    def get_service(self, obj):
        """ Return service details uri """
        return reverse(viewname='wapi:v2:waves-services-detail', request=self.context['request'],
                       kwargs={'service_app_name': obj.service.api_name})

    def get_queryset(self):
        """ Filter wapi:v2 enabled submissions """
        return Submission.objects.filter(availability=1)


from waves.models import JobInput


class SubmittedInputsSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobInput
        fields = ('api_name', 'job', 'value')


class ServiceSerializer(DynamicFieldsModelSerializer, serializers.HyperlinkedModelSerializer):
    """ Serialize a service """

    class Meta:
        model = Service
        fields = ('url', 'name', 'version', 'short_description', 'service_app_name',
                  'jobs', 'submissions', 'form', 'created', 'updated', 'inputs', 'title', "email_to")
        lookup_field = 'api_name'
        read_only_fields = ('url', 'name', 'version', 'short_description',
                            'jobs', 'submissions', 'form', 'created', 'updated')
        extra_kwargs = {
            'url': {'view_name': 'wapi:v2:waves-services-detail',
                    'lookup_field': 'api_name',
                    'lookup_url_kwarg': 'service_app_name'},
        }

    jobs = serializers.SerializerMethodField()
    submissions = serializers.SerializerMethodField()
    form = serializers.SerializerMethodField()
    service_app_name = serializers.CharField(source='api_name', read_only=True)
    inputs = SubmittedInputsSerializer(many=True, write_only=True, required=False)
    title = serializers.CharField(write_only=True, required=False)
    email_to = serializers.EmailField(write_only=True, required=False)

    def get_submissions(self, obj):
        return [
            {'submission_app_name': sub.api_name,
             'url': reverse(viewname='wapi:v2:waves-services-submission-detail', request=self.context['request'],
                            kwargs={'service_app_name': obj.api_name, 'submission_app_name': sub.api_name})} for
            sub in obj.submissions_api.all()]

    def get_form(self, obj):
        if obj.submissions_api.count() > 0:
            return reverse(viewname='wapi:v2:waves-services-form', request=self.context['request'],
                           kwargs={'service_app_name': obj.api_name})
        return ""

    def get_jobs(self, obj):
        """ return uri to access current service users' jobs """
        return reverse(viewname='wapi:v2:waves-services-jobs', request=self.context['request'],
                       kwargs={'service_app_name': obj.api_name})
