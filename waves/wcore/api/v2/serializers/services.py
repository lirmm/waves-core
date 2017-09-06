""" WAVES API services related serializers"""
from __future__ import unicode_literals

import swapper
from django.contrib.staticfiles.storage import staticfiles_storage
from rest_framework import serializers
from rest_framework.reverse import reverse as reverse

from waves.wcore.api.share import DynamicFieldsModelSerializer
from waves.wcore.models.services import Submission, SubmissionOutput
from waves.wcore.settings import waves_settings
from .inputs import InputSerializer as DetailInputSerializer

Service = swapper.load_model("wcore", "Service")

__all__ = ['OutputSerializer', 'ServiceSerializer', 'ServiceFormSerializer', 'ServiceSubmissionSerializer']


class OutputSerializer(DynamicFieldsModelSerializer):
    """ Serialize an service expected output """

    class Meta:
        model = SubmissionOutput
        fields = ('name', 'file_pattern')

    def to_representation(self, instance):
        """ Representation for a output """
        to_repr = {}
        for output in instance.all():
            to_repr[output.api_name] = {
                'label': output.name,
                'file_name': output.file_pattern
            }
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
        fields = ('name', 'inputs', 'outputs', 'form')
        extra_kwargs = {
            'api_name': {'view_name': 'wapi:api_v2:waves-submission-detail',
                         'lookup_fields': {'api_name', 'api_name'}},
        }

    view_name = 'wapi:api_v2:waves-submission-detail'
    # submission_uri = serializers.SerializerMethodField()
    inputs = InputSerializer(many=False, source="expected_inputs")
    form = serializers.SerializerMethodField()
    # service = serializers.SerializerMethodField()
    outputs = OutputSerializer(read_only=True, many=False)

    def get_form(self, obj):
        """ Return Service form endpoint uri"""
        return reverse(viewname='wapi:api_v2:waves-submission-detail', request=self.context['request'],
                       kwargs={'service': obj.service.api_name, 'api_name': obj.api_name}) + 'form'

    def get_submission_uri(self, obj):
        """ Returned service submission endpoint uri"""
        return reverse(viewname='wapi:api_v2:waves-services-submissions', request=self.context['request'],
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
                        kwargs={'service': obj.api_name, 'api_name': sub.api_name}) for sub in obj.submissions.all()]

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
        return [
            self.context['request'].build_absolute_uri(staticfiles_storage.url('waves/css/forms.css')), ]

    def get_js(self, obj):
        """ link to service js"""
        return [
            self.context['request'].build_absolute_uri(staticfiles_storage.url('waves/js/services.js')),
            self.context['request'].build_absolute_uri(staticfiles_storage.url('waves/js/api_services.js')),
        ]

    def get_form(self, obj):
        """ Create the form and return its content"""
        from waves.wcore.forms.services import ServiceSubmissionForm
        from waves.wcore.api.views.service import JobSubmissionView
        from django.shortcuts import render
        import re
        form = ServiceSubmissionForm(instance=self.instance, parent=self.instance.service)
        print form.helper.get_attributes()
        form.helper.form_tag = True
        view = JobSubmissionView()
        content = render(request=self.context['request'],
                         template_name='waves/api/service_api_form.html',
                         context={'form': form,
                                  'js': self.get_js(obj),
                                  'css': self.get_css(obj)},
                         content_type='')
        print content
        return re.sub(r'\s\s+', '', str(content))

    def get_post_uri(self, obj):
        """ Return expected form post uri """
        return reverse(viewname='wapi:api_v2:waves-services-submissions', request=self.context['request'],
                       kwargs={'api_name': obj.api_name, 'service': obj.service.api_name})

    def get_service(self, obj):
        """ Back-link to service wapi:api_v2 uri """
        return reverse(viewname='wapi:api_v2:waves-services-detail', request=self.context['request'],
                       kwargs={'api_name': obj.service.api_name})
