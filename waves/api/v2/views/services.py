"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the GNU GPL v3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       https://www.gnu.org/licenses/gpl-3.0.en.html
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import logging

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action, renderer_classes
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.renderers import StaticHTMLRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse

from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from waves.api.permissions import ServiceAccessPermission
from waves.api.v2 import serializers
from waves.core.exceptions import JobException
from waves.forms import frontend
from waves.models import Job, Service

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
    permission_classes = (ServiceAccessPermission,)
    # serializer_class = serializers.ServiceSerializer # overidden to handle multiple serializers in the same endpoint
    parser_classes = (MultiPartParser,)
    lookup_field = 'api_name'
    lookup_url_kwarg = 'service_app_name'

    def get_serializer_class(self):
        # handle multiple serializer in introspection schema
        method = self.action.split("_")
        if(method[0] == "submission"):
            return serializers.ServiceSubmissionSerializer
        return serializers.ServiceSerializer

    def get_queryset(self):
        """ retrieve available services for current request user """
        return Service.objects.get_services(user=self.request.user)

    def list(self, request, **kwargs):
        """ List all available services """
        serializer = serializers.ServiceSerializer(self.get_queryset(), many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """ Retrieve Service details"""
        service_tool = get_object_or_404(self.get_queryset(), api_name=kwargs.get('service_app_name'))
        serializer = serializers.ServiceSerializer(service_tool, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def jobs(self, request, service_app_name):
        """ Retrieves services Jobs """
        service_tool = get_object_or_404(self.get_queryset(), api_name=service_app_name)
        queryset_jobs = Job.objects.get_service_job(user=request.user, service=service_tool)
        serializer = serializers.JobSerializer(queryset_jobs, many=True, context={'request': request},
                                               hidden=['inputs', 'outputs', 'history'])
        return Response(serializer.data)

    @extend_schema(responses={(200, 'text/html'): OpenApiTypes.STR})
    @action(detail=True, methods=['get'])
    @renderer_classes((StaticHTMLRenderer,))
    def form(self, request, *args, **kwargs):
        """ Retrieve service form """
        from django.shortcuts import render
        from django.http import HttpResponse
        from waves.forms.frontend import ServiceSubmissionForm
        api_name = self.kwargs.get('service_app_name')
        service_tool = get_object_or_404(self.get_queryset(), api_name=api_name)
        form = [{'submission': service_submission,
                 'form': ServiceSubmissionForm(instance=service_submission,
                                               parent=service_tool,
                                               submit_ajax=True,
                                               form_action=request.build_absolute_uri(
                                                   reverse('wapi:v2:waves-services-submission-jobs',
                                                           kwargs=dict(
                                                               service_app_name=self.kwargs.get('service_app_name'),
                                                               submission_app_name=service_submission.api_name)
                                                           )))}
                for service_submission in service_tool.submissions_api.all()]

        content = render(request=self.request,
                         template_name='waves/api/service_api_form.html',
                         context={'submissions': form,
                                  'js': get_js(self),
                                  'css': get_css(self)},
                         content_type='')
        return HttpResponse(content=content, content_type="text/html; charset=utf8")

    @action(detail=True, methods=['get'], url_name='submission-detail',
            url_path="submissions/(?P<submission_app_name>[\w-]+)")
    def submission(self, request, service_app_name, submission_app_name):
        obj = self.get_object()
        submission = obj.submissions_api.filter(api_name=submission_app_name)
        serializer = serializers.ServiceSubmissionSerializer(many=False, instance=submission[0],
                                                             context={'request': self.request})
        return Response(serializer.data)

    @extend_schema(responses={(200, 'text/html'): OpenApiTypes.STR})
    @action(detail=True, methods=['get'], url_name="submission-form",
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
                 'form': frontend.ServiceSubmissionForm(instance=submission,
                                                        parent=submission.service,
                                                        submit_ajax=True,
                                                        template_pack=template_pack,
                                                        form_action=request.build_absolute_uri(
                                                            reverse('wapi:v2:waves-services-submission-jobs',
                                                                    kwargs=dict(
                                                                        service_app_name=service_app_name,
                                                                        submission_app_name=submission_app_name
                                                                    ))))}]
        content = render(request=self.request,
                         template_name='waves/api/service_api_form.html',
                         context={'submissions': form,
                                  'js': get_js(self)})
        return HttpResponse(content=content, content_type="text/html; charset=utf8")

    @extend_schema(responses={200: serializers.JobSerializer(many=True)})
    @action(detail=True, methods=['get'], url_name='submission-jobs',
            url_path="submissions/(?P<submission_app_name>[\w-]+)/jobs")
    def submission_jobs_list(self, request, service_app_name, submission_app_name, *args, **kwargs):
        service = self.get_object()
        obj = service.submissions_api.filter(api_name=submission_app_name)[0]
        queryset_jobs = Job.objects.get_submission_job(user=request.user, submission=obj)
        serializer = serializers.JobSerializer(queryset_jobs, many=True, context={'request': request},
                                               hidden=['inputs', 'outputs', 'history'])
        return Response(serializer.data)

    @extend_schema(responses={201: serializers.JobSerializer(many=False)})
    @action(detail=True, methods=['post'], url_name='submission-job-create',
            url_path="submissions/(?P<submission_app_name>[\w-]+)/jobs")
    def submission_jobs_create(self, request, service_app_name, submission_app_name, *args, **kwargs):
        service = self.get_object()
        obj = service.submissions_api.filter(api_name=submission_app_name)[0]

        # CREATE a new job for this submission
        logger.debug("Create Job")
        if logger.isEnabledFor(logging.DEBUG):
            for name, param in request.data.items():
                logger.debug('param key ' + name)
                logger.debug(param)
            logger.debug('Request Data %s', request.data)
        passed_data = request.data
        ass_email = passed_data.get('email', None)
        try:
            passed_data.get('api_key', None)
            # bad hack to allow openapi calls
            data = passed_data.get('params', passed_data)
            created_job = Job.objects.create_from_submission(submission=obj,
                                                             email_to=ass_email,
                                                             submitted_inputs=data,
                                                             user=self.request.user)
            # Now job is created (or raise an exception),
            serializer = serializers.JobSerializer(created_job, many=False, context={'request': request})
            # logger.debug(f'Job created {serializer.data}')
            logger.debug('Job successfully created %s ' % created_job.slug)
            return Response(serializer.data, status=201)
        except ValidationError as e:
            logger.warning("Validation error %s", e)
            raise DRFValidationError(e.message_dict)
        except JobException as e:
            logger.fatal("Create Error %s", e)
            return Response({'error': e}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: serializers.ServiceSubmissionSerializer(many=True)})
    @action(detail=True, methods=['get'], url_name='submissions')
    def submissions(self, request, service_app_name):
        obj = self.get_object()
        submission = obj.submissions_api.all()
        serializer = serializers.ServiceSubmissionSerializer(many=True, instance=submission,
                                                             context={'request': self.request})
        return Response(serializer.data)
