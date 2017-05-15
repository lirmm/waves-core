""" WAVES Service back-office Import view"""
from __future__ import unicode_literals

from django.db import DatabaseError
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.views.generic import View
from django.contrib import messages
from django.core.urlresolvers import reverse

from waves.admin.views.export import ModelExportView
from waves.models import Service
from waves.admin.views.runner_tool import RunnerImportToolView, ObjectDoesNotExist, RunnerTestConnectionView

# TODO in manage permission
# from django.contrib.auth.decorators import permission_required
# @permission_required('services.can_edit')
class ServiceParamImportView(RunnerImportToolView):
    """ Import view for Service from adaptor"""

    def get_object(self, request):
        try:
            self.object = Service.objects.get(id=self.kwargs.get('service_id'))
        except ObjectDoesNotExist as e:
            messages.error(request, message='Unable to retrieve runner from request')

    def get_form_kwargs(self):
        kwargs = super(ServiceParamImportView, self).get_form_kwargs()
        extra_kwargs = {
            'selected': self.object.remote_service_id
        }
        kwargs.update(extra_kwargs)
        return kwargs

    def remote_service_id(self, request):
        return self.object.remote_service_id


class ServiceDuplicateView(View):

    def get(self, request, *args, **kwargs):
        try:
            service = get_object_or_404(Service, id=kwargs['service_id'])
            new_service = service.duplicate()
            messages.add_message(request, level=messages.SUCCESS, message="Service successfully copied, "
                                                                          "you may edit it now")
            return redirect(reverse('admin:waves_service_change', args=[new_service.id]))
        except DatabaseError as e:
            messages.add_message(request, level=messages.WARNING, message="Error occurred during copy: %s " % e)
            return redirect(reverse('admin:waves_service_change', args=[kwargs['service_id']]))


class ServiceExportView(ModelExportView):
    """ Export Service representation in order to load it in another WAVES application """
    model = Service

    @property
    def return_view(self):
        return reverse('admin:waves_service_change', args=[self.object.id])


class ServiceTestConnectionView(RunnerTestConnectionView):
    model = Service

    def get_object_name(self):
        return self.object.runner.name

