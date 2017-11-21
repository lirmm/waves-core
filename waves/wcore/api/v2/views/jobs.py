""" WAVES API jobs endpoints """
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import detail_route
from rest_framework.parsers import MultiPartParser, JSONParser, BaseParser
from rest_framework.response import Response

from waves.wcore.api.views.base import WavesAuthenticatedView
from waves.wcore.exceptions import WavesException
from waves.wcore.models import Job, JobOutput
from waves.wcore.api.v2.serializers.jobs import JobSerializer, JobHistoryDetailSerializer, JobInputDetailSerializer, \
    JobOutputDetailSerializer
from django.http import HttpResponse, HttpResponseNotFound
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin


class JobViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin,
                 viewsets.GenericViewSet, WavesAuthenticatedView):
    """
    API entry point for ServiceJobs
    """
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    parser_classes = (MultiPartParser, JSONParser)
    lookup_field = 'slug'
    filter_fields = ('_status', 'updated')

    def get_queryset(self):
        """
        Basic job queryset
        :return: querySet
        base_queryset = super(JobViewSet, self).get_queryset()
        queryset = Job.objects.add_filter_user(base_queryset, self.request.user).order_by('-created')
        return queryset
        """
        return Job.objects.get_user_job(self.request.user).order_by('-created')

    def retrieve(self, request, slug=None, *args, **kwargs):
        """ Detailed job info """
        service_job = get_object_or_404(self.get_queryset(), slug=slug)
        serializer = JobSerializer(service_job, context={'request': request})
        return Response(serializer.data)

    def destroy(self, request, slug=None, *args, **kwargs):
        """ Try to remotely cancel job, then delete it from WAVES DB """
        service_job = get_object_or_404(self.get_queryset(), slug=slug)
        try:
            service_job.run_cancel()
        except WavesException as e:
            pass
        self.perform_destroy(service_job)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['get'], url_path='history')
    def list_history(self, request, slug=None):
        """ List job history elements """
        queryset = Job.objects.get_user_job(user=request.user)
        job = get_object_or_404(queryset, slug=slug)
        serializer = JobHistoryDetailSerializer(job, many=False, context={'request': request})
        return Response(serializer.data)

    @detail_route(methods=['get'], url_path='inputs')
    def list_inputs(self, request, slug=None):
        """ list job submitted inputs """
        queryset = Job.objects.get_user_job(user=request.user)
        job = get_object_or_404(queryset, slug=slug)
        serializer = JobInputDetailSerializer(job, many=False, context={'request': request})
        return Response(serializer.data)

    @detail_route(methods=['get'], url_path='outputs')
    def list_outputs(self, request, slug=None):
        """ list job expected outputs """
        queryset = Job.objects.get_user_job(user=request.user)
        job = get_object_or_404(queryset, slug=slug)
        serializer = JobOutputDetailSerializer(job, many=False, context={'request': request})
        return Response(serializer.data)


class PlainTextParser(BaseParser):
    """
        Plain text parser.
        """
    media_type = 'text/plain'

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Simply return a string representing the body of the request.
        """
        return stream.read()


class JobOutputRawView(SingleObjectMixin, View):
    model = JobOutput

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            with open(instance.file_path) as fp:
                file_content = fp.read()
                o_content = file_content.decode('utf-8')
        except IOError as e:
            return HttpResponseNotFound('Content not available')
        return HttpResponse(content=o_content, content_type="text/plain; charset=utf8")
