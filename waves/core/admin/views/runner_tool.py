""" WAVES runner backoffice tools"""
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, FormView

from json_view import JSONDetailView
from waves.core.adaptors.exceptions import AdaptorConnectException
from waves.core.admin.forms.services import ImportForm
from waves.core.admin.views.export import ModelExportView
from waves.core.exceptions import RunnerException
from waves.core.models import Runner
from waves.core.models import get_service_model

Service = get_service_model()


class RunnerImportToolView(DetailView, FormView):
    """ Import a new service for a runner """
    template_name = 'waves/admin/import/service_modal_form.html'
    form_class = ImportForm
    model = Runner
    # success_url = '/admin/import/tools/2'
    success_message = "Data successfully imported"
    service = None
    importer = None
    tool_list = ()
    object = None
    context_object_name = 'context_object'

    def get_context_data(self, **kwargs):
        context = super(RunnerImportToolView, self).get_context_data(**kwargs)
        self.tool_list = self.get_tool_list()
        return context

    def get_success_url(self):
        return self.service.get_admin_url()

    def get_tool_list(self):
        return self.get_object().importer.list_services()

    def get_service_list(self):
        return self.get_object().running_services.all()

    def get_form(self, form_class=None):
        form = self.form_class(instance=self.get_object())
        return form

    def get(self, request, *args, **kwargs):
        try:
            self.tool_list = self.get_tool_list()
            if len(self.tool_list) == 0:
                messages.info(request, "No tool retrieved")
        except RunnerException as exc:
            messages.error(request, message="Connection error to remote adapter %s" % exc)
        except NotImplementedError:
            messages.error(request, message="This adapter does not allow service import")
            if settings.DEBUG:
                raise
        except Exception as e:
            messages.error(request, message="Unexpected error %s " % e)
            if settings.DEBUG:
                raise
        return super(RunnerImportToolView, self).get(request, *args, **kwargs)

    def remote_service_id(self, request):
        return request.POST.get('tool')

    def form_invalid(self, form):
        return super(RunnerImportToolView, self).form_invalid(form)

    def post(self, request, *args, **kwargs):
        runner = self.get_object()
        tool_id = self.remote_service_id(self.request)
        importer = runner.importer
        try:
            with transaction.atomic():
                update_service = self.request.POST.get('update_service', False)
                if self.request.POST.get('running_services', None):
                    service = Service.objects.get(pk=self.request.POST.get('running_services'))
                else:
                    service = None
                self.service, new_submission = importer.import_service(tool_id, service, update_service)
                if service is None:
                    # New service, set up runner at service level
                    self.service.runner = runner
                    self.service.created_by = request.user
                    self.service.runner.adaptor_params.filter(name='command').update(value=tool_id)
                    self.service.save()
                    data = {'url_redirect': self.service.get_admin_url()}
                else:
                    # Existing service, setup runner at submission level
                    new_submission.runner = runner
                    new_submission.runner.adaptor_params.filter(name='command').update(value=tool_id)
                    new_submission.save()
                    data = {'url_redirect': new_submission.get_admin_url()}
                if len(importer.warnings) > 0:
                    message = "<b>Import with warnings :-( </b><br/>- "
                    message += "<br/>- ".join(["%s" % warning.message for warning in importer.warnings])
                    messages.add_message(self.request, level=messages.INFO, message=mark_safe(message))
                if len(importer.errors) > 0:
                    message = "<b>Import with errors :-( </b><br/>- "
                    message += "<br/>- ".join(["%s" % err.message for err in importer.errors])
                    messages.add_message(self.request, level=messages.ERROR, message=mark_safe(message))
                if len(importer.warnings) == 0 and len(importer.errors) == 0:
                    messages.add_message(self.request, level=messages.SUCCESS, message='All parameters imported :-)')
                messages.add_message(self.request, level=messages.INFO,
                                     message="Import log in %s" % importer.log_file)
                return JsonResponse(data, status=200)
        except Exception as e:
            data = {'url_redirect': runner.get_admin_url()}
            messages.add_message(self.request, level=messages.ERROR,
                                 message=mark_safe("Import failed :-( :<pre>%s</pre>" % e.message))
            messages.add_message(self.request, level=messages.INFO,
                                 message="Import log in %s" % importer.log_file)
            return JsonResponse(data, status=200)


class RunnerExportView(ModelExportView):
    """ Export Service representation in order to load it in another WAVES application """
    model = Runner

    @property
    def return_view(self):
        return reverse('admin:wcore_runner_change', args=[self.object.id])


class RunnerTestConnectionView(JSONDetailView):
    template_name = None
    model = Runner
    adaptor = None
    runner_model = None

    def get_object(self, queryset=None):
        obj = super(RunnerTestConnectionView, self).get_object(queryset)
        self.adaptor = obj.adaptor
        return obj

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
