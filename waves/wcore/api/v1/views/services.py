""" WAVES API services end points """
from __future__ import unicode_literals

import logging

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework import viewsets, generics
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from waves.wcore.api.v1.serializers import ServiceSerializer, JobSerializer, ServiceFormSerializer, \
    ServiceSubmissionSerializer
from waves.wcore.api.views.base import WavesAuthenticatedView
from waves.wcore.exceptions.jobs import JobException
from waves.wcore.models import Job, Submission as ServiceSubmission
from waves.wcore.models.services import get_service_model

Service = get_service_model()

logger = logging.getLogger(__name__)


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API entry point to Services (Retrieve, job submission)
    """
    serializer_class = ServiceSerializer
    lookup_field = 'api_name'

    def get_queryset(self):
        """ retrieve available services for current request user """
        return Service.objects.get_api_services(user=self.request.user)

    @list_route(methods=['get'], permission_classes=[AllowAny])
    def list_services(self, request):
        """ List all available services """
        serializer = ServiceSerializer(self.get_queryset(), many=True, context={'request': request},
                                       fields=('url', 'name', 'short_description',
                                               'version', 'created', 'updated', 'jobs'))
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """ Retrieve Service details"""
        api_name = kwargs.pop('api_name')
        service_tool = get_object_or_404(self.get_queryset(), api_name=api_name)
        serializer = ServiceSerializer(service_tool, context={'request': request})
        return Response(serializer.data)

    @detail_route(methods=['get'], url_path='jobs')
    def service_job(self, request, api_name=None):
        """ Retrieves services Jobs """
        service_tool = get_object_or_404(self.get_queryset(), api_name=api_name)
        queryset_jobs = Job.objects.get_service_job(user=request.user, service=service_tool)
        serializer = JobSerializer(queryset_jobs, many=True, context={'request': request},
                                   fields=('url', 'created', 'status', 'service'))
        return Response(serializer.data)

    @detail_route(methods=['get'], url_path="form")
    def service_form(self, request, api_name=None):
        """ Retrieve service form """
        service_tool = get_object_or_404(self.get_queryset(), api_name=api_name)
        serializer = ServiceFormSerializer(many=False, context={'request': request}, instance=service_tool)
        return Response(serializer.data)


class MultipleFieldLookupMixin(object):
    """ Some view with multiple url kwargs """

    def get_object(self):
        """ Retrieve an object from multiple field retrieved from kwargs """
        queryset = self.get_queryset()  # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filters = {}
        for field in self.lookup_fields:
            filters[field] = self.kwargs[field]
        return get_object_or_404(queryset, **filters)  # Lookup the object


class ServiceJobSubmissionView(MultipleFieldLookupMixin, generics.CreateAPIView,
                               WavesAuthenticatedView):
    """ Service job Submission view """
    queryset = ServiceSubmission.objects.all()
    serializer_class = ServiceSubmissionSerializer
    lookup_fields = ('service', 'api_name')

    def get_queryset(self):
        """ Retrieve for service, current submissions available for API """
        return ServiceSubmission.objects.filter(api_name=self.kwargs.get('api_name'),
                                                service__api_name=self.kwargs.get('service'), availability__gte=2)

    def get_object(self):
        """ Retrieve object or redirect to 404 """
        return get_object_or_404(self.get_queryset())

    def post(self, request, *args, **kwargs):
        """ Create a new job from submitted params """
        if logger.isEnabledFor(logging.DEBUG):
            for param in request.data:
                logger.debug('param key ' + param)
                logger.debug(request.data[param])
            logger.debug('Request Data %s', request.data)
        service_submission = self.get_object()
        ass_email = request.data.pop('email', None)
        try:
            request.data.pop('api_key', None)
            from ..serializers.jobs import JobCreateSerializer
            from django.db.models import Q
            job = Job.objects.create_from_submission(submission=service_submission, email_to=ass_email,
                                                     submitted_inputs=request.data, user=request.user)
            # Now job is created (or raise an exception),
            serializer = JobSerializer(job, many=False, context={'request': request},
                                       fields=('slug', 'url', 'created', 'status',))
            return Response(serializer.data, status=201)
        except ValidationError as e:
            raise DRFValidationError(e.message_dict)
        except JobException as e:
            logger.fatal("Create Error %s", e.message)
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)


class ServiceJobSubmissionViewForm(ServiceJobSubmissionView):
    """ Service Form content view """

    def get(self, request, *args, **kwargs):
        """ GET accessor """
        submission = self.get_object()
        serializer = ServiceFormSerializer(many=False, context={'request': request}, instance=submission)
        return Response(serializer.data)
