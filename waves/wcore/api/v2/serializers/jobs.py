# -*- coding: utf-8 -*-
""" Jobs API serializers """
from __future__ import unicode_literals

from os import stat
from os.path import getsize, isfile

import swapper
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.reverse import reverse

from waves.wcore.api.share import DynamicFieldsModelSerializer
from waves.wcore.models import JobInput, Job, JobOutput, AParam, JobHistory

Service = swapper.load_model("wcore", "Service")

User = get_user_model()


class JobHistorySerializer(DynamicFieldsModelSerializer):
    """ JobHistory Serializer - display status / message / timestamp """

    class Meta:
        model = JobHistory
        fields = ('status_txt', 'status_code', 'timestamp', 'message')

    status_txt = serializers.SerializerMethodField()
    status_code = serializers.IntegerField(source='status')

    @staticmethod
    def get_status_txt(history):
        """ return status text """
        return history.get_status_display()


class JobHistoryDetailSerializer(serializers.HyperlinkedModelSerializer):
    """ Job history serializer """

    class Meta:
        model = Job
        fields = ('job', 'last_status', 'last_status_txt', 'job_history')
        extra_kwargs = {
            'url': {'view_name': 'wapi:api_v2:waves-jobs-detail', 'lookup_field': 'slug'}
        }

    last_status = serializers.IntegerField(source='status')
    last_status_txt = serializers.SerializerMethodField()
    job_history = JobHistorySerializer(many=True, read_only=True, source="public_history")
    job = serializers.SerializerMethodField()

    def get_job(self, obj):
        return reverse(viewname='wapi:api_v2:waves-jobs-detail', request=self.context['request'],
                       kwargs={'slug': obj.slug})

    @staticmethod
    def get_last_status_txt(obj):
        """ return status text """
        return obj.get_status_display()


class JobInputSerializer(DynamicFieldsModelSerializer):
    """ JobInput serializer """

    class Meta:
        model = JobInput
        fields = ('name', 'label', 'value')
        # depth = 1

    # input = serializers.SerializerMethodField()

    def get_input(self, obj):
        """ Return input label """
        return obj.label

    def to_representation(self, instance):
        """ Representation for a output """
        to_repr = []
        for j_input in instance.all():
            repres = {
                'name': j_input.api_name,
                "label": j_input.label,
                'param_type': j_input.type,
                "value": j_input.value,
            }
            if j_input.type == AParam.TYPE_FILE:
                repres["download_uri"] = self.get_download_url(j_input.slug)
            to_repr.append(repres)
        return to_repr

    def get_download_url(self, slug):
        """ Link to jobOutput download uri """
        return "%s?export=1" % reverse(viewname='wapi:api_v2:waves-job-input', request=self.context['request'],
                                       kwargs={'slug': slug})


class JobInputDetailSerializer(serializers.HyperlinkedModelSerializer):
    """ Job Input Details serializer """

    class Meta:
        model = Job
        fields = ('job', 'inputs')
        extra_kwargs = {
            'url': {'view_name': 'wapi:api_v2:waves-jobs-detail', 'lookup_field': 'slug'}
        }
    inputs = JobInputSerializer(source='job_inputs', read_only=True)
    job = serializers.SerializerMethodField()

    def get_job(self, obj):
        return reverse(viewname='wapi:api_v2:waves-jobs-detail', request=self.context['request'],
                       kwargs={'slug': obj.slug})


class JobOutputSerializer(serializers.ModelSerializer):
    """ JobOutput serializer """

    class Meta:
        model = JobOutput
        fields = ('name', 'download_url', 'content')

    download_url = serializers.SerializerMethodField()

    def file_get_content(self, file_path):
        """ Either returns output content, or text of content size exceeds 500ko"""
        if not isfile(file_path) or stat(file_path).st_size == 0:
            return None
        if getsize(file_path) < 500:
            with open(file_path) as fp:
                file_content = fp.read()
            return file_content.decode()
        return ""

    def to_representation(self, instance):
        """ Representation for a output """
        from waves.wcore.utils import normalize_value
        to_repr = {}
        for output in instance:
            to_repr[normalize_value(output.get_api_name())] = {
                "name": output.name,
                "raw": self.get_raw_url(output.slug),
                "download_uri": self.get_download_url(output.slug),
                "content": self.file_get_content(output.file_path)
            }
        return to_repr

    def get_download_url(self, slug):
        """ Link to jobOutput download uri """
        return "%s?export=1" % reverse(viewname='wapi:api_v2:waves-job-output', request=self.context['request'],
                                       kwargs={'slug': slug})

    def get_raw_url(self, slug):
        """ Link to jobOutput download uri """
        return "%s" % reverse(viewname='wapi:api_v2:waves-job-output-raw',
                              request=self.context['request'],
                              kwargs={'slug': slug})


class JobOutputDetailSerializer(serializers.HyperlinkedModelSerializer):
    """ JobOutput List serializer """

    class Meta:
        model = Job
        fields = ('job', 'outputs')
        extra_kwargs = {
            'url': {'view_name': 'wapi:api_v2:waves-jobs-detail', 'lookup_field': 'slug'}
        }

    outputs = JobOutputSerializer(read_only=True, source='output_files')

    def get_job(self, obj):
        return reverse(viewname='wapi:api_v2:waves-jobs-detail', request=self.context['request'],
                       kwargs={'slug': obj.slug})

    job = serializers.SerializerMethodField()
    @staticmethod
    def get_status_txt(obj):
        """ Return job status text """
        return obj.get_status_display()


class JobSerializer(DynamicFieldsModelSerializer, serializers.HyperlinkedModelSerializer):
    """ Serializer for Job (only GET) """

    class Meta:
        model = Job
        fields = ('url', 'slug', 'title', 'status_code', 'status_txt', 'created', 'updated', 'inputs', 'outputs',
                  'history', 'client', 'service')
        read_only_fields = (
            'status_code', 'status_txt', 'slug', 'client', 'service', 'created', 'updated', 'url', 'history')
        extra_kwargs = {
            'url': {'view_name': 'wapi:api_v2:waves-jobs-detail', 'lookup_field': 'slug'}
        }
        depth = 1
        lookup_field = 'slug'

    status_txt = serializers.SerializerMethodField()
    status_code = serializers.IntegerField(source='status')
    client = serializers.StringRelatedField(many=False, read_only=False)
    history = serializers.SerializerMethodField()
    outputs = serializers.SerializerMethodField()
    inputs = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()

    def get_service(self, obj):
        if obj.submission and obj.submission.service:
            return reverse(viewname='wapi:api_v2:waves-services-detail', request=self.context['request'],
                           kwargs={'api_name': obj.submission.service.api_name})
        else:
            return obj.service

    def get_history(self, obj):
        """ Link to job history details wapi:api_v2 endpoint """
        return reverse(viewname='wapi:api_v2:waves-jobs-history', request=self.context['request'],
                       kwargs={'slug': obj.slug})

    def get_outputs(self, obj):
        """ Link to job outputs wapi:api_v2 endpoint """
        return reverse(viewname='wapi:api_v2:waves-jobs-outputs', request=self.context['request'],
                       kwargs={'slug': obj.slug})

    def get_inputs(self, obj):
        """ Link to job inputs wapi:api_v2 endpoint """
        return reverse(viewname='wapi:api_v2:waves-jobs-inputs', request=self.context['request'],
                       kwargs={'slug': obj.slug})

    @staticmethod
    def get_status_txt(job):
        """ Return string corresponding to status code """
        return job.get_status_display()


class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ('job_inputs', 'submission')
        write_only_fields = ('job_inputs',)

    def create(self, validated_data):
        return Job.objects.create()
