""" WAVES API jobs endpoints """

import logging
from os.path import getsize

import magic
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from waves.api.v2 import serializers
from waves.core.exceptions.jobs import JobInconsistentStateError
from waves.core.models import Job

logger = logging.getLogger(__name__)


class JobFileView(object):

    @staticmethod
    def response(instance):
        if hasattr(instance, 'file_path'):
            try:
                mime = magic.Magic(mime=True)
                mime_type = mime.from_file(instance.file_path)
                with open(instance.file_path) as fp:
                    if 'text' or 'x-empty' in mime_type:
                        response = Response(data=fp.read())
                    else:
                        response = HttpResponse(content=fp)
                        response['Content-Type'] = mime_type
                        response['Content-Length'] = getsize(instance.file_path)
                        response['Content-Disposition'] = 'attachment; filename=%s' % instance.file_name
                return response
            except IOError:
                # Do nothing, by default return 404 if error
                return HttpResponseNotFound('File do not exists')
        return HttpResponseNotFound('Content not available')


@permission_classes((IsAuthenticated,))
class JobViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.DestroyModelMixin,
                 viewsets.GenericViewSet):
    """
    API entry point for ServiceJobs
    """
    serializer_class = serializers.JobSerializer
    queryset = Job.objects.all()
    parser_classes = (JSONParser,)
    lookup_field = 'slug'
    lookup_url_kwarg = 'unique_id'
    filter_fields = ('_status', 'updated', 'submission')
    http_method_names = ['get', 'options', 'post', 'delete']

    @action(detail=True, methods=['post'], url_path="cancel")
    def cancel(self, request, unique_id):
        """
        Update Job according to requested action
        """
        job = self.get_object()
        if job.client != self.request.user:
            return HttpResponseForbidden("Action not allowed")
        try:
            job.run_cancel()
        except JobInconsistentStateError as e:
            perm = PermissionDenied(detail=e.message)
            perm.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
            raise perm
        return Response({'success': 'Job marked as cancelled'}, status=status.HTTP_202_ACCEPTED)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve detailed WAVES job info
        """
        return super(JobViewSet, self).retrieve(request, *args, **kwargs)

    @permission_classes((IsAuthenticated,))
    def list(self, request, *args, **kwargs):
        """
        List current jobs related to user, require to be logged in
        """
        queryset = Job.objects.get_user_job(user=request.user)
        serializer = self.get_serializer(queryset, many=True, hidden=['inputs', 'outputs', 'history'])
        return Response(serializer.data)

    @permission_classes((IsAuthenticated,))
    def destroy(self, request, *args, **kwargs):
        """
        Try to cancel job, then delete it from database, can't be undone

        """
        job = self.get_object()
        try:
            job.run_cancel()
        except JobInconsistentStateError as e:
            # Even if we can't cancel job, delete it from db, so let it run on adaptor.
            pass
        return super(JobViewSet, self).destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def status(self, request, *args, **kwargs):
        job = self.get_object()
        serializer = serializers.JobStatusSerializer(instance=job)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_name='output-detail', url_path="outputs/(?P<app_short_name>[\w-]+)")
    @permission_classes((IsAuthenticated,))
    def output(self, request, unique_id, app_short_name):
        job = self.get_object()
        instance = job.outputs.filter(api_name=app_short_name)
        if instance:
            return JobFileView.response(instance[0])
        else:
            return NotFound('Not found')

    @action(detail=True, methods=['get'], url_path="outputs$")
    def outputs(self, request, unique_id):
        job = self.get_object()
        serializer = serializers.JobOutputSerializer(instance=job.outputs.all(), context={'request': self.request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path="inputs$")
    def inputs(self, request, unique_id):
        """ List all inputs for this job
        """
        job = self.get_object()
        serializer = serializers.JobInputSerializer(instance=job.job_inputs.all(),
                                                    context={'request': self.request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_name='input-detail', url_path="inputs/(?P<app_short_name>[\w-]+)")
    @permission_classes((IsAuthenticated,))
    def input(self, request, unique_id, app_short_name):
        job = self.get_object()
        instance = job.job_inputs.filter(api_name=app_short_name)
        if instance:
            return JobFileView.response(instance[0])
        else:
            return NotFound('Not found')
