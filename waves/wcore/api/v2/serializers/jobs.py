# -*- coding: utf-8 -*-
""" Jobs API serializers """
from __future__ import unicode_literals

from collections import OrderedDict
from os.path import isfile

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.reverse import reverse

from waves.wcore.api.share import DynamicFieldsModelSerializer
from waves.wcore.models import JobInput, Job, JobOutput, JobHistory, get_service_model
from waves.wcore.models.const import ParamType

Service = get_service_model()
User = get_user_model()


class JobStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        field = ('status',)

    def to_representation(self, instance):
        return OrderedDict({
            'status': instance.status,
            'status_code': instance.status,
            'label': instance.get_status_display()
        })


class JobUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', )


class JobHistorySerializer(DynamicFieldsModelSerializer):
    """ JobHistory Serializer - display status / message / timestamp """

    class Meta:
        model = JobHistory
        ordering = ('-created',)
        fields = ('status_txt', 'status_code', 'timestamp', 'message')

    status_txt = serializers.SerializerMethodField()
    status_code = serializers.IntegerField(source='status')

    @staticmethod
    def get_status_txt(history):
        """ return status text """
        return history.get_status_display()


class JobInputSerializer(DynamicFieldsModelSerializer):
    """ JobInput serializer """

    class Meta:
        model = JobInput
        fields = ('name', 'label', 'value')
        # depth = 1

    def to_representation(self, instance):
        """ Representation for a output """
        to_repr = {}
        for j_input in instance.all():
            repres = OrderedDict({
                'name': j_input.api_name,
                "label": j_input.label,
                'param_type': j_input.param_type,
                "value": j_input.value,
            })
            if j_input.param_type == ParamType.TYPE_FILE:
                repres["url"] = reverse(viewname='wapi:v2:waves-jobs-input-detail', request=self.context['request'],
                                        kwargs={
                                            'unique_id': j_input.job.slug,
                                            'app_short_name': j_input.api_name
                                        })
            to_repr[j_input.api_name] = repres
        return to_repr

    def to_internal_value(self, data):
        return super(JobInputSerializer, self).to_internal_value(data)


class JobOutputSerializer(serializers.ModelSerializer):
    """
    JobOutput serializer
    Serialize a JobOutput, return a dictionary indexed by output api_name(s)
    """

    class Meta:
        model = JobOutput
        fields = ('name', 'download_url', 'content')

    content = serializers.FileField(read_only=True, source="file_content")

    def get_url(self, output):
        if isfile(output.file_path):
            return reverse(viewname='wapi:v2:waves-jobs-output-detail', request=self.context['request'],
                           kwargs={
                               'unique_id': output.job.slug,
                               'app_short_name': output.api_name})
        else:
            return None

    def to_representation(self, instance):
        """ Representation for a output """
        to_repr = {}
        for output in instance:
            to_repr[output.api_name] = OrderedDict([
                ("label", output.name),
                ("file_name", output.file_name),
                ("extension", output.get_extension()),
                ("url", self.get_url(output)),
            ])
        return to_repr


class JobSerializer(DynamicFieldsModelSerializer,
                    serializers.HyperlinkedModelSerializer):
    """ Serializer for Job (only GET) """

    class Meta:
        model = Job
        fields = ('url', 'slug', 'title', 'service', 'submission', 'client', 'status', 'created',
                  'updated', 'inputs', 'outputs', 'history', 'last_message')
        read_only_fields = (
            'title', 'status', 'status_code', 'status_txt', 'slug', 'client', 'service', 'created', 'updated', 'url',
            'history')
        extra_kwargs = {
            'url': {'view_name': 'wapi:v2:waves-jobs-detail', 'lookup_field': 'slug', 'lookup_url_kwarg': 'unique_id'}
        }
        lookup_field = 'slug'

    service = serializers.SerializerMethodField(read_only=True)
    submission = serializers.SerializerMethodField(read_only=True)
    status = serializers.SerializerMethodField(source='_status', read_only=True)
    client = serializers.CharField(read_only=True, source="email_to")
    history = JobHistorySerializer(many=True, read_only=True, source="public_history")
    outputs = JobOutputSerializer(read_only=True, source='output_files')
    inputs = JobInputSerializer(source='job_inputs', read_only=True)
    last_message = JobHistorySerializer(source='last_history', many=False, fields=['timestamp', 'message'],
                                        read_only=True)

    def get_submission(self, obj):
        if obj.submission and obj.submission.service:
            return reverse(viewname='wapi:v2:waves-services-submission-detail', request=self.context['request'],
                           kwargs={'service_app_name': obj.submission.service.api_name,
                                   'submission_app_name': obj.submission.api_name})
        else:
            return obj.service

    def get_service(self, obj):
        if obj.submission and obj.submission.service:
            return reverse(viewname='wapi:v2:waves-services-detail', request=self.context['request'],
                           kwargs={'service_app_name': obj.submission.service.api_name})
        else:
            return obj.service

    def get_history(self, obj):
        """ Link to job history details wapi:v2 endpoint """
        return reverse(viewname='wapi:v2:waves-jobs-history', request=self.context['request'],
                       kwargs={'slug': obj.slug})

    def get_status(self, obj):
        """ Return string corresponding to status code """
        return {
            'code': obj.status,
            'label': obj.get_status_display()
        }
