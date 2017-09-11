""" WAVES API services end points """
from __future__ import unicode_literals

import logging

import swapper
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets, generics
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from waves.wcore.api.v2.serializers.jobs import JobSerializer
from waves.wcore.api.v2.serializers.services import ServiceSerializer, ServiceSubmissionSerializer
from waves.wcore.api.views.base import WavesAuthenticatedView
from waves.wcore.exceptions.jobs import JobException
from waves.wcore.models import Job
from waves.wcore.models.services import Submission
from waves.wcore.views.services import ServiceSubmissionForm

Service = swapper.load_model("wcore", "Service")

logger = logging.getLogger(__name__)


def get_css(obj):
    """ link to service css """
    return [
        obj.request.build_absolute_uri(staticfiles_storage.url('waves/css/forms.css')), ]


def get_js(obj):
    """ link to service js"""
    return [
        obj.request.build_absolute_uri(staticfiles_storage.url('waves/js/services.js')),
        obj.request.build_absolute_uri(staticfiles_storage.url('waves/js/api_services.js')),
    ]


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API entry point to Services (Retrieve, job submission)
    """
    serializer_class = ServiceSerializer
    lookup_field = 'api_name'

    def get_queryset(self):
        """ retrieve available services for current request user """
        return Service.objects.get_api_services(user=self.request.user)

    def list(self, request):
        """ List all available services """
        serializer = ServiceSerializer(self.get_queryset(), many=True, context={'request': request},
                                       fields=('url', 'name', 'short_description',
                                               'version', 'created', 'updated', 'form', 'submissions', 'jobs'))
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
        from django.shortcuts import render
        from django.http import HttpResponse
        from waves.wcore.forms.services import ServiceSubmissionForm
        service_tool = get_object_or_404(self.get_queryset(), api_name=api_name)
        form = [{'submission': service_submission,
                 'form': ServiceSubmissionForm(instance=service_submission, parent=service_tool)}
                for service_submission in
                service_tool.submissions.all()]
        content = render(request=self.request,
                         template_name='waves/api/service_api_form.html',
                         context={'submissions': form,
                                  'js': get_js(self),
                                  'css': get_css(self)},
                         content_type='')
        return HttpResponse(content=content, content_type="text/plain; charset=utf8")


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


class ServiceJobSubmissionView(MultipleFieldLookupMixin, generics.RetrieveAPIView, generics.CreateAPIView,
                               WavesAuthenticatedView):
    """ Service job Submission view """
    queryset = Submission.objects.all()
    serializer_class = ServiceSubmissionSerializer
    lookup_fields = ('service', 'api_name')

    def get_queryset(self):
        """ Retrieve for service, current submissions available for API """
        return Submission.objects.filter(api_name=self.kwargs.get('api_name'),
                                         service__api_name=self.kwargs.get('service'), availability__gt=2)

    def get_object(self):
        """ Retrieve object or redirect to 404 """
        return get_object_or_404(self.get_queryset())

    # TODO add check authorization
    def post(self, request, *args, **kwargs):
        """ Create a new job from submitted params """
        logger.debug("Entering base post data")
        if logger.isEnabledFor(logging.DEBUG):
            for param in request.data:
                logger.debug('param key ' + param)
                logger.debug(request.data[param])
            logger.debug('Request Data %s', request.data)
        service_submission = self.get_object()
        ass_email = request.data.pop('email', None)
        try:
            request.data.pop('api_key', None)
            from waves.wcore.api.v2.serializers.jobs import JobCreateSerializer
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


class ServiceSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSubmissionSerializer
    lookup_field = 'api_name'
    # http_method_names = ['get', 'post', 'options']

    def get_queryset(self):
        """ Retrieve for service, current submissions available for API """
        return Submission.objects.filter(service__api_name=self.kwargs.get('service'),
                                         availability__gt=2)

    @detail_route(methods=['get'], url_path="form")
    def submission_form(self, request, service=None, api_name=None, **kwargs):
        """ Retrieve service form """
        service_tool = get_object_or_404(self.get_queryset(), api_name=api_name)
        template_pack = self.request.GET.get('tp', 'bootstrap3')
        form = [{'submission': service_tool,
                 'form': ServiceSubmissionForm(instance=self.get_object(), parent=service_tool,
                                               template_pack=template_pack)}]
        content = render(request=self.request,
                         template_name='waves/api/service_api_form.html',
                         context={'submissions': form,
                                  'js': get_js(self),
                                  'css': get_css(self)})
        return HttpResponse(content=content, content_type="text/plain; charset=utf8")

    @detail_route(methods=['post'])
    def create_job(self, request, *args, **kwargs):
        """ Create a new job from submitted params """
        logger.debug("in detail route")
        if logger.isEnabledFor(logging.DEBUG):
            for param in request.data:
                logger.debug('param key ' + param)
                logger.debug(request.data[param])
            logger.debug('Request Data %s', request.data)
        service_submission = self.get_object()
        ass_email = request.data.pop('email', None)
        try:
            request.data.pop('api_key', None)
            from waves.wcore.api.v2.serializers.jobs import JobCreateSerializer
            from django.db.models import Q
            job = Job.objects.create_from_submission(submission=service_submission, email_to=ass_email,
                                                     submitted_inputs=request.data, user=request.user)
            # Now job is created (or raise an exception),
            serializer = JobSerializer(job, many=False, context={'request': request},
                                       fields=('slug', 'url', 'created', 'status',))
            logger.debug('Job created %s ' % job.slug)
            return Response(serializer.data, status=201)
        except ValidationError as e:
            logger.warning("Validation error " + e)
            raise DRFValidationError(e.message_dict)
        except JobException as e:
            logger.fatal("Create Error %s", e.message)
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
