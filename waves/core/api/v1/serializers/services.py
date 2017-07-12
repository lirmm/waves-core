""" WAVES API services related serializers"""
from __future__ import unicode_literals

import logging

from django.contrib.staticfiles.storage import staticfiles_storage
from rest_framework.reverse import reverse as reverse

from waves.core.api.v1.serializers.inputs import *
from waves.core.models import SubmissionOutput as ServiceOutput, Service, \
    Submission as ServiceSubmission
from waves.core.settings import waves_settings

__all__ = ['InputSerializer', 'InputSerializer', 'OutputSerializer', 'ServiceSerializer',
           'ServiceFormSerializer', 'ServiceSubmissionSerializer']
logger = logging.getLogger(__name__)


class InputFormatField(serializers.Field):
    def __init__(self, read_only=False, write_only=False, required=None, default=empty, initial=empty, source=None,
                 label=None, help_text=None, style=None, error_messages=None, validators=None, allow_null=False):
        super(InputFormatField, self).__init__(read_only, write_only, required, default, initial, source, label,
                                               help_text, style, error_messages, validators, allow_null)

    def to_representation(self, instance):
        return ', '.join(instance.splitlines()) if instance is not None else ''

    def to_internal_value(self, data):
        return data.replace(', ', '\n') if data else ''


class OutputSerializer(DynamicFieldsModelSerializer):
    """ Serialize an service expected output """

    class Meta:
        model = ServiceOutput
        fields = ('name', 'ext', 'may_be_empty', 'file_pattern')


class ServiceSubmissionSerializer(DynamicFieldsModelSerializer, serializers.HyperlinkedRelatedField):
    """ Serialize a Service submission """

    class Meta:
        model = ServiceSubmission
        fields = ('label', 'service', 'submission_uri', 'form', 'inputs')
        extra_kwargs = {
            'api_name': {'view_name': 'waves:api_v1:waves-submission-detail',
                         'lookup_fields': {'api_name', 'api_name'}},
        }

    view_name = 'waves:api_v1:waves-services-submissions'
    submission_uri = serializers.SerializerMethodField()
    inputs = InputSerializer(many=True, source="expected_inputs")
    form = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()
    label = serializers.CharField(source='name')

    def get_form(self, obj):
        """ Return Service form endpoint uri"""
        return reverse(viewname='waves:api_v1:waves-services-submissions-form', request=self.context['request'],
                       kwargs={'service': obj.service.api_name, 'api_name': obj.api_name})

    def get_submission_uri(self, obj):
        """ Returned service submission endpoint uri"""
        return reverse(viewname='waves:api_v1:waves-services-submissions', request=self.context['request'],
                       kwargs={'service': obj.service.api_name,
                               'api_name': obj.api_name})

    def get_service(self, obj):
        """ Return service details uri """
        return reverse(viewname='waves:api_v1:waves-services-detail', request=self.context['request'],
                       kwargs={'api_name': obj.service.api_name})

    def get_queryset(self):
        """ Filter api enabled submissions """
        return ServiceSubmission.objects.filter(available_api=True)


class ServiceSerializer(serializers.HyperlinkedModelSerializer, DynamicFieldsModelSerializer):
    """ Serialize a service """

    class Meta:
        model = Service
        fields = ('url', 'name', 'version', 'created', 'short_description', 'default_submission_uri',
                  'jobs', 'submissions')
        lookup_field = 'api_name'
        extra_kwargs = {
            'url': {'view_name': 'waves:api_v1:waves-services-detail', 'lookup_field': 'api_name'},
        }

    jobs = serializers.SerializerMethodField()
    submissions = ServiceSubmissionSerializer(many=True, read_only=True, hidden=('service',))
    default_submission_uri = serializers.SerializerMethodField()

    def get_default_submission_uri(self, obj):
        """ Return service default submission uri """
        if obj.default_submission_api is not None:
            return reverse(viewname='waves:api_v1:waves-services-submissions', request=self.context['request'],
                           kwargs={'service': obj.api_name, 'api_name': obj.default_submission_api.api_name})
        else:
            logger.warning('Service %s has no default submission', obj)
            return ""

    def get_jobs(self, obj):
        """ return uri to access current service users' jobs """
        return reverse(viewname='waves:api_v1:waves-services-jobs', request=self.context['request'],
                       kwargs={'api_name': obj.api_name})


class ServiceFormSerializer(serializers.ModelSerializer):
    """ Service form serializer """

    class Meta:
        model = ServiceSubmission
        fields = ('label', 'service', 'js', 'css', 'template_pack', 'post_uri', 'form')

    js = serializers.SerializerMethodField()
    css = serializers.SerializerMethodField()
    form = serializers.SerializerMethodField()
    post_uri = serializers.SerializerMethodField()
    template_pack = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()
    label = serializers.CharField(source='name')

    def get_template_pack(self, obj):
        return waves_settings.TEMPLATE_PACK

    def get_css(self, obj):
        """ link to service css """
        return self.context['request'].build_absolute_uri(staticfiles_storage.url('waves/css/forms.css'))

    def get_js(self, obj):
        """ link to service js"""
        return self.context['request'].build_absolute_uri(staticfiles_storage.url('waves/js/services.js'))

    def get_form(self, obj):
        """ Create the form and return its content"""
        from waves.core.forms.services import ServiceSubmissionForm
        from django.template import RequestContext
        import re
        form = ServiceSubmissionForm(instance=self.instance, parent=self.instance.service)
        return re.sub(r'\s\s+', '', form.helper.render_layout(form, context=RequestContext(self.context['request'])))

    def get_post_uri(self, obj):
        """ Return expected form post uri """
        return reverse(viewname='waves:api_v1:waves-services-submissions', request=self.context['request'],
                       kwargs={'api_name': obj.api_name, 'service': obj.service.api_name})

    def get_service(self, obj):
        """ Back-link to service api uri """
        return reverse(viewname='waves:api_v1:waves-services-detail', request=self.context['request'],
                       kwargs={'api_name': obj.service.api_name})
