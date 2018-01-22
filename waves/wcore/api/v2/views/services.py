""" WAVES API services end points """
from __future__ import unicode_literals

import logging

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route, renderer_classes
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.renderers import StaticHTMLRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse

from waves.wcore.api.v2.serializers.jobs import JobSerializer
from waves.wcore.api.v2.serializers.services import ServiceSerializer, ServiceSubmissionSerializer
from waves.wcore.exceptions.jobs import JobException
from waves.wcore.models import Job, get_service_model, get_submission_model
from waves.wcore.views.services import ServiceSubmissionForm

Submission = get_submission_model()
Service = get_service_model()

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


class ServiceViewSet(viewsets.ModelViewSet):
    """
    API entry point to Services (Retrieve, job submission)
    """
    permission_classes = (AllowAny, )
    serializer_class = ServiceSerializer
    lookup_field = 'api_name'
    lookup_url_kwarg = 'service_app_name'

    def get_queryset(self):
        """ retrieve available services for current request user """
        return Service.objects.get_services(user=self.request.user)

    def list(self, request, **kwargs):
        """ List all available services """
        serializer = ServiceSerializer(self.get_queryset(), many=True, context={'request': request},
                                       fields=('url', 'name', 'short_description',
                                               'version', 'created', 'updated', 'form', 'submissions', 'jobs'))
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """ Retrieve Service details"""
        service_tool = get_object_or_404(self.get_queryset(), api_name=kwargs.get('service_app_name'))
        serializer = ServiceSerializer(service_tool, context={'request': request})
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def jobs(self, request, *args, **kwargs):
        """ Retrieves services Jobs """
        service_tool = get_object_or_404(self.get_queryset(), api_name=self.kwargs.get('service_app_name'))
        queryset_jobs = Job.objects.get_service_job(user=request.user, service=service_tool)
        serializer = JobSerializer(queryset_jobs, many=True, context={'request': request},
                                   hidden=['inputs', 'outputs', 'history'])
        return Response(serializer.data)

    @detail_route(methods=['get'])
    @renderer_classes((StaticHTMLRenderer,))
    def form(self, request, *args, **kwargs):
        """ Retrieve service form """
        from django.shortcuts import render
        from django.http import HttpResponse
        from waves.wcore.forms.services import ServiceSubmissionForm
        api_name = self.kwargs.get('service_app_name')
        service_tool = get_object_or_404(self.get_queryset(), api_name=api_name)
        form = [{'submission': service_submission,
                 'form': ServiceSubmissionForm(instance=service_submission,
                                               parent=service_tool,
                                               submit_ajax=True,
                                               form_action=request.build_absolute_uri(
                                                   reverse('wapi:v2:waves-services-submission-detail',
                                                           kwargs=dict(
                                                               service_app_name=self.kwargs.get('service_app_name'),
                                                               submission_app_name=service_submission.api_name)
                                                           )) + '/jobs')}
                for service_submission in service_tool.submissions_api.all()]

        content = render(request=self.request,
                         template_name='waves/api/service_api_form.html',
                         context={'submissions': form,
                                  'js': get_js(self),
                                  'css': get_css(self)},
                         content_type='')
        return HttpResponse(content=content, content_type="text/html; charset=utf8")

    @detail_route(methods=['get'], url_name='submission-detail', url_path="submissions/(?P<submission_app_name>[\w-]+)")
    def submission(self, request, service_app_name, submission_app_name):
        obj = self.get_object()
        submission = obj.submissions_api.filter(api_name=submission_app_name)
        serializer = ServiceSubmissionSerializer(many=False, instance=submission[0], context={'request': self.request})
        return Response(serializer.data)

    @detail_route(methods=['get'], url_name="submission-form",
                  url_path="submissions/(?P<submission_app_name>[\w-]+)/form")
    @renderer_classes((StaticHTMLRenderer,))
    def submission_form(self, request, service_app_name, submission_app_name):
        """
        Retrieve service form as raw html

        Allows to include this part of generated code inside any HTML page

        Submission is made on API.
        """
        obj = self.get_object()
        submission = obj.submissions_api.filter(api_name=submission_app_name)[0]
        template_pack = self.request.GET.get('tp', 'bootstrap3')
        form = [{'submission': submission,
                 'form': ServiceSubmissionForm(instance=submission,
                                               parent=submission.service,
                                               request=self.request,
                                               template_pack=template_pack,
                                               form_action=request.build_absolute_uri(
                                                   reverse('wapi:v2:waves-services-submission-detail',
                                                           kwargs=dict(
                                                               service_app_name=service_app_name,
                                                               submission_app_name=submission_app_name
                                                           ))) + '/jobs')}]
        content = render(request=self.request,
                         template_name='waves/api/service_api_form.html',
                         context={'submissions': form,
                                  'js': get_js(self),
                                  'css': get_css(self)})
        return HttpResponse(content=content, content_type="text/html; charset=utf8")

    @detail_route(methods=['get', 'post'], url_name='submission-jobs',
                  url_path="submissions/(?P<submission_app_name>[\w-]+)/jobs")
    def submission_jobs(self, request, service_app_name, submission_app_name):
        service = self.get_object()
        obj = service.submissions_api.filter(api_name=submission_app_name)[0]
        if self.request.method == 'GET':
            queryset_jobs = Job.objects.get_submission_job(user=request.user, submission=obj)
            serializer = JobSerializer(queryset_jobs, many=True, context={'request': request},
                                       hidden=['inputs', 'outputs', 'history'])
            return Response(serializer.data)
        elif self.request.method == 'POST':
            # CREATE a new job for this submission
            logger.debug("Create Job")
            if logger.isEnabledFor(logging.DEBUG):
                for param in request.data:
                    logger.debug('param key ' + param)
                    logger.debug(request.data[param])
                logger.debug('Request Data %s', request.data)
            passed_data = request.data.copy()
            ass_email = passed_data.pop('email_to', None)
            try:
                passed_data.pop('api_key', None)
                created_job = Job.objects.create_from_submission(submission=obj,
                                                                 email_to=ass_email,
                                                                 submitted_inputs=passed_data,
                                                                 user=self.request.user)

                # Now job is created (or raise an exception),
                serializer = JobSerializer(created_job, many=False, context={'request': request},
                                           fields=('slug', 'url', 'created', 'status', 'service', 'submission'))
                logger.debug('Job successfully created %s ' % created_job.slug)
                return Response(serializer.data, status=201)
            except ValidationError as e:
                logger.warning("Validation error %s", e)
                raise DRFValidationError(e.message_dict)
            except JobException as e:
                logger.fatal("Create Error %s", e.message)
                return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)


class ServiceSubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    jobs:
    Interact with jobs

    """
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = ServiceSubmissionSerializer
    lookup_url_kwarg = 'submission_app_name'
    lookup_field = 'api_name'
    http_method_names = ['get', 'options', 'post']

    def get_object_or_404(self):
        return get_object_or_404(Submission, service__api_name=self.kwargs.get('service_app_name'),
                                 api_name=self.kwargs.get('submission_app_name'))

    def get_queryset(self):
        """ Retrieve for service, current submissions available for API """
        return Submission.objects.filter(service__api_name=self.kwargs.get('service_app_name'),
                                         api_name=self.kwargs.get('submission_app_name'),
                                         availability=1)

    def retrieve(self, request, *args, **kwargs):
        """
        Get Service submission detailed informations (inputs, parameters, expected outputs)

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        submission = self.get_object_or_404()
        serializer = ServiceSubmissionSerializer(instance=submission, context={'request': request})
        return Response(serializer.data)

    @detail_route(methods=['get'])
    @renderer_classes((StaticHTMLRenderer,))
    def form(self, request, *args, **kwargs):
        """
        Retrieve service form as raw html

        Allows to include this part of generated code inside any HTML page

        Submission is made on API.
        """
        service_api_name = self.kwargs.get('service_app_name')
        submission_api_name = self.kwargs.get('submission_app_name')
        submission = self.get_object_or_404()
        template_pack = self.request.GET.get('tp', 'bootstrap3')
        form = [{'submission': submission,
                 'form': ServiceSubmissionForm(instance=self.get_object_or_404(),
                                               parent=submission.service,
                                               template_pack=template_pack,
                                               submit_ajax=True,
                                               form_action=request.build_absolute_uri(
                                                   reverse('wapi:v2:waves-services-submission-detail',
                                                           kwargs=dict(
                                                               service_app_name=service_api_name,
                                                               submission_app_name=submission_api_name
                                                           ))) + '/jobs')}]
        content = render(request=self.request,
                         template_name='waves/api/service_api_form.html',
                         context={'submissions': form,
                                  'js': get_js(self),
                                  'css': get_css(self)})
        return HttpResponse(content=content, content_type="text/html; charset=utf8")

    def list(self, request, *args, **kwargs):
        """
        List all available submissions for this service

        :return: A list of currently available submissions
        """
        return super(ServiceSubmissionViewSet, self).list(request, *args, **kwargs)

    @detail_route(methods=['get', 'post'], url_path='jobs')
    def jobs(self, request, *args, **kwargs):
        """
        get:
        Return a list of current user's job for this submission

        post:
        Create a new job from submitted inputs

        :param request: HTTP request
        :return: list
        """
        obj = self.get_object_or_404()
        if self.request.method == 'GET':
            queryset_jobs = Job.objects.get_submission_job(user=request.user, submission=obj)
            serializer = JobSerializer(queryset_jobs, many=True, context={'request': request},
                                       fields=['url', 'slug', 'title', 'status', 'created', 'updated', 'last_message'])
            return Response(serializer.data)
        elif self.request.method == 'POST':
            # CREATE a new job for this submission
            logger.debug("Create Job")
            if logger.isEnabledFor(logging.DEBUG):
                for param in request.data:
                    logger.debug('param key ' + param)
                    logger.debug(request.data[param])
                logger.debug('Request Data %s', request.data)
            passed_data = request.data.copy()
            ass_email = passed_data.pop('email_to', None)
            try:
                passed_data.pop('api_key', None)
                created_job = Job.objects.create_from_submission(submission=obj,
                                                                 email_to=ass_email,
                                                                 submitted_inputs=passed_data,
                                                                 user=self.request.user)

                # Now job is created (or raise an exception),
                serializer = JobSerializer(created_job, many=False, context={'request': request},
                                           fields=('slug', 'url', 'created', 'status', 'service', 'submission'))
                logger.debug('Job successfully created %s ' % created_job.slug)
                return Response(serializer.data, status=201)
            except ValidationError as e:
                logger.warning("Validation error %s", e)
                raise DRFValidationError(e.message_dict)
            except JobException as e:
                logger.fatal("Create Error %s", e.message)
                return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
