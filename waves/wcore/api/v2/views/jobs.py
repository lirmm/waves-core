""" WAVES API jobs endpoints """
from __future__ import unicode_literals

import logging
from os.path import getsize

import magic
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import detail_route
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from waves.wcore.api.v2.serializers.jobs import JobSerializer
from waves.wcore.exceptions.jobs import JobInconsistentStateError
from waves.wcore.models import Job, JobOutput, JobInput

logger = logging.getLogger(__name__)


class JobViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.DestroyModelMixin,
                 viewsets.GenericViewSet):
    """
    API entry point for ServiceJobs
    """
    serializer_class = JobSerializer
    queryset = Job.objects.all()
    parser_classes = (JSONParser,)
    lookup_field = 'slug'
    filter_fields = ('_status', 'updated', 'submission')
    http_method_names = ['get', 'options', 'put', 'delete']

    @detail_route(methods=['put'], url_path="cancel", permission_classes=(IsAuthenticated,))
    def cancel(self, request, slug):
        """
        Update Job according to requested action
        """
        # TODO check permissions
        job = get_object_or_404(self.get_queryset(), slug=slug)
        try:
            job.run_cancel()
        except JobInconsistentStateError as e:
            perm = PermissionDenied(detail=e.message)
            perm.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
            raise perm
        return Response({'success': 'Job marked as cancelled'}, status=status.HTTP_202_ACCEPTED)

    def retrieve(self, request, slug=None):
        """
        Detailed job info
        """
        queryset = get_object_or_404(self.get_queryset(), slug=slug)
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)

    def list(self, request):
        """
        :param request:
        :return:
        """
        queryset = Job.objects.get_user_job(user=request.user)
        serializer = self.get_serializer(queryset, many=True, hidden=['inputs', 'outputs', 'history'])
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Try to cancel job if needed, then delete it from db
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        job = get_object_or_404(self.get_queryset())
        try:
            job.run_cancel()
        except JobInconsistentStateError as e:
            # Even if we can't cancel job, delete it from db, so let it run on adaptor.
            pass
        return super(JobViewSet, self).destroy(request, *args, **kwargs)


class JobFileView(SingleObjectMixin):

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if hasattr(instance, 'file_path'):
            try:
                mime = magic.Magic(mime=True)
                with open(instance.file_path) as fp:
                    response = HttpResponse(content=fp)
                    response['Content-Type'] = mime.from_file(instance.file_path)
                    response['Content-Length'] = getsize(instance.file_path)
                    response['Content-Disposition'] = 'attachment; filename=%s' \
                                                      % instance.file_name
                return response
            except IOError:
                # Do nothing, by default return 404 if error
                pass
        return HttpResponseNotFound('Content not available')


class JobOutputView(JobFileView, View):
    model = JobOutput


class JobInputView(JobFileView, View):
    model = JobInput
