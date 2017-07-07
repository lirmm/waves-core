""" WAVES runner backoffice tools"""
from __future__ import unicode_literals

from crispy_forms.utils import render_crispy_form
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import JsonResponse
from django.views.generic import FormView
from json_view import JSONDetailView
from waves.adaptors.exceptions import AdaptorConnectException
from waves.exceptions import *
from waves.admin.forms.services import ImportForm
from waves.models import Runner, Submission, get_service_model
from waves.admin.views.export import ModelExportView

Service = get_service_model()

class RunnerImportToolView(FormView):
    """ Import a new service for a runner """
    template_name = 'admin/waves/import/service_modal_form.html'
    form_class = ImportForm
    # success_url = '/admin/import/tools/2'
    success_message = "Data successfully imported"
    service = None
    importer = None
    tool_list = ()
    object = None
    context_object_name = 'context_object'

    def get_object(self, request):
        try:
            self.object = Runner.objects.get(id=self.kwargs.get('runner_id'))
        except ObjectDoesNotExist as e:
            messages.error(request, message='Unable to retrieve runner from request')

    def get_context_data(self, **kwargs):
        context = super(FormView, self).get_context_data(**kwargs)
        context['context_object_name'] = self.object.name
        return context

    def get_success_url(self):
        # return reverse('admin:waves_service_change', args=[self.service.id])
        return self.service.get_admin_url()

    def get_tool_list(self):
        return [(x[0], [(y.remote_service_id, y.name + ' ' + y.version) for y in x[1]]) for x in
                self.object.importer.list_services()]

    def get(self, request, *args, **kwargs):
        self.get_object(request)
        if self.object is None:
            return super(FormView, self).get(request, *args, **kwargs)
        try:
            self.tool_list = self.get_tool_list()
            if len(self.tool_list) == 0:
                messages.info(request, "No tool retrieved")
        except RunnerException as exc:
            messages.error(request, message="Connection error to remote adaptor %s" % exc)
        except NotImplementedError:
            messages.error(request, message="This adaptor does not allow service import")
            if settings.DEBUG:
                raise
        except Exception as e:
            messages.error(request, message="Unexpected error %s " % e)
            if settings.DEBUG:
                raise
        return super(FormView, self).get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(FormView, self).get_form_kwargs()
        extra_kwargs = {
            'tool': self.tool_list
        }
        extra_kwargs.update(kwargs)
        return extra_kwargs

    def remote_service_id(self, request):
        return request.POST.get('tool')

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            self.get_object(request)
            if self.object is None:
                return super(FormView, self).get(request, *args, **kwargs)
            self.tool_list = self.get_tool_list()
            form = self.get_form()
            if form.is_valid():
                try:
                    with transaction.atomic():
                        service_dto = self.object.importer.import_service(self.remote_service_id(request))
                        self.service = Service.objects.create()
                        self.service.from_dto(service_dto)
                        self.service.runner = self.object
                        self.service.created_by = self.request.user
                        submission = Submission.objects.create(name='Imported submission', service=self.service)
                        self.service.submissions.add(submission)
                        for inp in service_dto.inputs:
                            new_input = Submission.objects.create(submission=submission)
                            new_input.from_dto(inp)
                            new_input.save()
                            submission.submission_inputs.add(new_input)
                        self.service.save()
                    data = {
                        # 'url_redirect': reverse('admin:waves_service_change', args=[self.service.id])
                        'url_redirect': self.service.get_admin_url()
                    }
                    messages.add_message(request, level=messages.SUCCESS, message='Parameters successfully imported')
                    return JsonResponse(data, status=200)
                except Exception as e:
                    form.add_error(None, ValidationError(message="Import Error: %s" % e))
                    form_html = render_crispy_form(form)
                    return JsonResponse({'form_html': form_html}, status=500)
            else:
                form.add_error(None, ValidationError(message="Missing data"))
                form_html = render_crispy_form(form)
                return JsonResponse({'form_html': form_html}, status=400)
        else:
            pass


class RunnerExportView(ModelExportView):
    """ Export Service representation in order to load it in another WAVES application """
    model = Runner

    @property
    def return_view(self):
        return reverse('admin:waves_runner_change', args=[self.object.id])


class RunnerTestConnectionView(JSONDetailView):
    template_name = None
    model = Runner
    adaptor = None
    runner_model = None

    def get_object(self, queryset=None):
        self.object = super(RunnerTestConnectionView, self).get_object(queryset)
        self.adaptor = self.object.adaptor
        return self.object

    def get_object_name(self):
        return self.object.name

    def get_data(self, context):
        context = {'connection_result': 'Failed :'}
        message = '<ul class="messagelist"><li class="{}">{}</li></ul>'
        try:
            if self.adaptor.test_connection():
                context['connection_result'] = message.format('success',
                                                              'Connexion successful to %s' %
                                                              self.get_object_name())
            else:
                raise AdaptorConnectException('Unknown error')
        except AdaptorConnectException as e:
            context['connection_result'] = message.format('error', "Adaptor connection error %s" % e)
        except Exception as e:
            context['connection_result'] = message.format('error', "Unexpected error %s " % e)
        return context
