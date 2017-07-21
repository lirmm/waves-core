""" WAVES API services related serializers"""
from __future__ import unicode_literals

from django.contrib.staticfiles.storage import staticfiles_storage
from rest_framework import serializers
from rest_framework.reverse import reverse as reverse

from waves.wcore.api.share import DynamicFieldsModelSerializer
from waves.wcore.models.services import get_service_model
from waves.wcore.models.submissions import *
from waves.wcore.settings import waves_settings
from .inputs import InputSerializer

Service = get_service_model()

__all__ = ['OutputSerializer', 'ServiceSerializer', 'ServiceFormSerializer', 'ServiceSubmissionSerializer']


class OutputSerializer(DynamicFieldsModelSerializer):
    """ Serialize an service expected output """

    class Meta:
        model = SubmissionOutput
        fields = ('name', 'file_pattern')


class ServiceSubmissionSerializer(DynamicFieldsModelSerializer, serializers.HyperlinkedRelatedField):
    """ Serialize a Service submission """

    class Meta:
        model = Submission
        fields = ('name', 'service', 'submission_uri', 'form', 'inputs')
        extra_kwargs = {
            'api_name': {'view_name': 'waves:api_v2:waves-submission-detail',
                         'lookup_fields': {'api_name', 'api_name'}},
        }

    view_name = 'waves:api_v2:waves-services-submissions'
    submission_uri = serializers.SerializerMethodField()
    inputs = InputSerializer(many=True, source="expected_inputs")
    form = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()

    def get_form(self, obj):
        """ Return Service form endpoint uri"""
        return reverse(viewname='waves:api_v2:waves-services-submissions-form', request=self.context['request'],
                       kwargs={'service': obj.service.api_name, 'api_name': obj.api_name})

    def get_submission_uri(self, obj):
        """ Returned service submission endpoint uri"""
        return reverse(viewname='waves:api_v2:waves-services-submissions', request=self.context['request'],
                       kwargs={'service': obj.service.api_name,
                               'api_name': obj.api_name})

    def get_service(self, obj):
        """ Return service details uri """
        return reverse(viewname='waves:api_v2:waves-services-detail', request=self.context['request'],
                       kwargs={'api_name': obj.service.api_name})

    def get_queryset(self):
        """ Filter waves:api_v2 enabled submissions """
        return Submission.objects.filter(availability__gt=2)


class ServiceSerializer(serializers.HyperlinkedModelSerializer, DynamicFieldsModelSerializer):
    """ Serialize a service """

    class Meta:
        model = Service
        fields = ('url', 'name', 'version', 'created', 'short_description', 'default_submission_uri',
                  'jobs', 'submissions')
        lookup_field = 'api_name'
        extra_kwargs = {
            'url': {'view_name': 'waves:api_v2:waves-services-detail', 'lookup_field': 'api_name'},
        }

    jobs = serializers.SerializerMethodField()
    submissions = ServiceSubmissionSerializer(many=True, read_only=True, hidden=('service',))
    default_submission_uri = serializers.SerializerMethodField()

    def get_default_submission_uri(self, obj):
        """ Return service default submission uri """
        if obj.default_submission_api is not None:
            return reverse(viewname='waves:api_v2:waves-services-submissions', request=self.context['request'],
                           kwargs={'service': obj.api_name, 'api_name': obj.default_submission_api.api_name})
        else:
            return ""

    def get_jobs(self, obj):
        """ return uri to access current service users' jobs """
        return reverse(viewname='waves:api_v2:waves-services-jobs', request=self.context['request'],
                       kwargs={'api_name': obj.api_name})


class ServiceFormSerializer(serializers.ModelSerializer):
    """ Service form serializer """

    class Meta:
        model = Submission
        fields = ('name', 'service', 'js', 'css', 'template_pack', 'post_uri', 'form')

    js = serializers.SerializerMethodField()
    css = serializers.SerializerMethodField()
    form = serializers.SerializerMethodField()
    post_uri = serializers.SerializerMethodField()
    template_pack = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()

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
        from waves.wcore.forms.services import ServiceSubmissionForm
        from django.template import RequestContext
        import re
        form = ServiceSubmissionForm(instance=self.instance, parent=self.instance.service)
        return re.sub(r'\s\s+', '', form.helper.render_layout(form, context=RequestContext(self.context['request'])))

    def get_post_uri(self, obj):
        """ Return expected form post uri """
        return reverse(viewname='waves:api_v2:waves-services-submissions', request=self.context['request'],
                       kwargs={'api_name': obj.api_name, 'service': obj.service.api_name})

    def get_service(self, obj):
        """ Back-link to service waves:api_v2 uri """
        return reverse(viewname='waves:api_v2:waves-services-detail', request=self.context['request'],
                       kwargs={'api_name': obj.service.api_name})
