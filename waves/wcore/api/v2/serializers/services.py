""" WAVES API services related serializers"""
from __future__ import unicode_literals

import collections

from rest_framework import serializers
from rest_framework.reverse import reverse

from waves.wcore.api.share import DynamicFieldsModelSerializer
from waves.wcore.api.v2.serializers.inputs import InputSerializer as DetailInputSerializer
from waves.wcore.models import get_service_model, get_submission_model
from waves.wcore.models.services import SubmissionOutput

Service = get_service_model()
Submission = get_submission_model()

__all__ = ['OutputSerializer', 'ServiceSerializer', 'ServiceSubmissionSerializer']


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
                    ('edam_data', output.edam_data)
                ]
                if hasattr(output, 'from_input') and output.from_input is not None:
                    tmp_repr.append(('issued_from', output.from_input.api_name))
                to_repr[output.api_name] = collections.OrderedDict(tmp_repr)
        return to_repr


class InputSerializer(DetailInputSerializer):
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

    inputs = InputSerializer(many=False, read_only=True, source='expected_inputs')
    form = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()
    jobs = serializers.SerializerMethodField()
    outputs = OutputSerializer(read_only=True, many=False)
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


class ServiceSerializer(DynamicFieldsModelSerializer, serializers.HyperlinkedModelSerializer):
    """ Serialize a service """

    class Meta:
        model = Service
        fields = ('url', 'name', 'version', 'short_description', 'service_app_name',
                  'jobs', 'submissions', 'form', 'created', 'updated')
        lookup_field = 'api_name'
        extra_kwargs = {
            'url': {'view_name': 'wapi:v2:waves-services-detail',
                    'lookup_field': 'api_name',
                    'lookup_url_kwarg': 'service_app_name'},
        }

    jobs = serializers.SerializerMethodField()
    submissions = serializers.SerializerMethodField()
    form = serializers.SerializerMethodField()
    service_app_name = serializers.CharField(source='api_name')

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
