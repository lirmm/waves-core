""" WAVES API services related serializers"""
from __future__ import unicode_literals

import collections

from rest_framework import serializers
from rest_framework.reverse import reverse

from waves.wcore.api.share import DynamicFieldsModelSerializer
from waves.wcore.models import get_service_model, get_submission_model
from waves.wcore.models.services import SubmissionOutput
from .inputs import InputSerializer as DetailInputSerializer

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
        for output in instance.all():
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
        fields = ('service', 'name', 'api_name', 'submission_uri', 'form', 'inputs', 'outputs', 'title')

    view_name = 'wapi:api_v2:waves-submission-detail'
    inputs = InputSerializer(many=False, source="expected_inputs")
    form = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()
    outputs = OutputSerializer(read_only=True, many=False)
    name = serializers.CharField(read_only=True)
    api_name = serializers.CharField(read_only=True)
    title = serializers.CharField(write_only=True)
    submission_uri = serializers.SerializerMethodField()

    def get_form(self, obj):
        """ Return Service form endpoint uri"""
        return reverse(viewname='wapi:api_v2:waves-submission-detail', request=self.context['request'],
                       kwargs={'service': obj.service.api_name, 'api_name': obj.api_name}) + 'form'

    def get_submission_uri(self, obj):
        """ Returned service submission endpoint uri"""
        return '%screate_job/' % reverse(viewname='wapi:api_v2:waves-submission-detail',
                                         request=self.context['request'],
                                         kwargs={'service': obj.service.api_name,
                                                 'api_name': obj.api_name})

    def get_service(self, obj):
        """ Return service details uri """
        return reverse(viewname='wapi:api_v2:waves-services-detail', request=self.context['request'],
                       kwargs={'api_name': obj.service.api_name})

    def get_queryset(self):
        """ Filter wapi:api_v2 enabled submissions """
        return Submission.objects.filter(availability__gt=2)


class ServiceSerializer(serializers.HyperlinkedModelSerializer, DynamicFieldsModelSerializer):
    """ Serialize a service """

    class Meta:
        model = Service
        fields = ('url', 'name', 'version', 'created', 'short_description',
                  'jobs', 'submissions', 'form')
        lookup_field = 'api_name'
        extra_kwargs = {
            'url': {'view_name': 'wapi:api_v2:waves-services-detail', 'lookup_field': 'api_name'},
        }

    jobs = serializers.SerializerMethodField()
    # submissions = ServiceSubmissionSerializer(many=True, read_only=True, hidden=('service',))
    submissions = serializers.SerializerMethodField()
    # default_submission_uri = serializers.SerializerMethodField()
    form = serializers.SerializerMethodField()

    def get_submissions(self, obj):
        return [reverse(viewname='wapi:api_v2:waves-submission-detail', request=self.context['request'],
                        kwargs={'service': obj.api_name, 'api_name': sub.api_name}) for sub in
                obj.submissions_api.all()]

    def get_form(self, obj):
        return reverse(viewname='wapi:api_v2:waves-services-detail', request=self.context['request'],
                       kwargs={'api_name': obj.api_name}) + 'form'

    def get_default_submission_uri(self, obj):
        """ Return service default submission uri """
        if obj.default_submission_api is not None:
            return reverse(viewname='wapi:api_v2:waves-services-submissions', request=self.context['request'],
                           kwargs={'service': obj.api_name, 'api_name': obj.default_submission_api.api_name})
        else:
            return ""

    def get_jobs(self, obj):
        """ return uri to access current service users' jobs """
        return reverse(viewname='wapi:api_v2:waves-services-jobs', request=self.context['request'],
                       kwargs={'api_name': obj.api_name})
