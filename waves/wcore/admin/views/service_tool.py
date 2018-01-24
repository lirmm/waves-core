# -*- coding: utf-8 -*-
""" WAVES Service back-office Import view"""
from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import DatabaseError

from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.views import generic
from django.views.generic import View
from django.core.exceptions import ObjectDoesNotExist
from waves.wcore.admin.views.export import ModelExportView
from waves.wcore.admin.views.runner_tool import RunnerImportToolView, RunnerTestConnectionView
from waves.wcore.models import get_service_model
from waves.wcore.settings import waves_settings
from waves.wcore.views.services import SubmissionFormView

Service = get_service_model()


# TODO in manage permission
# from django.contrib.auth.decorators import permission_required
# @permission_required('services.can_edit')
class ServiceParamImportView(RunnerImportToolView):
    """ Import view for Service from adaptor"""

    def get_object(self, queryset=None):
        try:
            self.object = Service.objects.get(id=self.kwargs.get('service_id'))
        except ObjectDoesNotExist as e:
            messages.error(self.request, message='Unable to retrieve runner from request')

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
            return redirect(reverse('admin:wcore_service_change', args=[new_service.id]))
        except DatabaseError as e:
            messages.add_message(request, level=messages.WARNING, message="Error occurred during copy: %s " % e)
            return redirect(reverse('admin:wcore_service_change', args=[kwargs['service_id']]))


class ServiceExportView(ModelExportView):
    """ Export Service representation in order to load it in another WAVES application """
    model = Service

    @property
    def return_view(self):
        return self.object.get_admin_url()
        # return reverse('admin:waves_service_change', args=[self.object.id])


class ServiceTestConnectionView(RunnerTestConnectionView):
    model = Service

    def get_object_name(self):
        return self.object.runner.name


class ServicePreviewForm(SubmissionFormView):
    template_name = 'waves/admin/service/service_preview.html'

    def get_context_data(self, **kwargs):
        context = super(ServicePreviewForm, self).get_context_data(**kwargs)
        context['template_pack'] = self.request.POST.get('template_pack', waves_settings.TEMPLATE_PACK)
        return context


class ServiceModalPreview(generic.DetailView):
    model = Service
    context_object_name = 'service'
    queryset = Service.objects.all().prefetch_related('submissions')
    object = None
    template_name = 'waves/admin/service/service_modal.html'

    def get_context_data(self, **kwargs):
        context = super(ServiceModalPreview, self).get_context_data(**kwargs)
        return context
