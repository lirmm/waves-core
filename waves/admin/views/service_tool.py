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

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
from django.views.generic import View

from waves.models import Service
from waves.settings import waves_settings
from waves.views import SubmissionFormView
from .export import ModelExportView
from .runner_tool import RunnerImportToolView, RunnerTestConnectionView

__all__ = ['ServiceParamImportView', 'ServiceExportView', 'ServiceModalPreview', 'ServicePreviewForm',
           'ServiceTestConnectionView', 'ServiceDuplicateView']


class ServiceParamImportView(RunnerImportToolView):
    """ Import view for Service from adapter"""

    def get_object(self, queryset=None):
        try:
            self.object = Service.objects.get(id=self.kwargs.get('service_id'))
        except ObjectDoesNotExist as e:
            messages.error(self.request, message='Unable to retrieve runner from request %s' % e)

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
    def get(self, request):
        try:
            service = get_object_or_404(Service, id=self.kwargs.get('service_id'))
            new_service = service.duplicate()
            messages.add_message(request, level=messages.SUCCESS, message="Service successfully copied, "
                                                                          "you may edit it now")
            return redirect(reverse('admin:waves_service_change', args=[new_service.id]))
        except DatabaseError as e:
            messages.add_message(request, level=messages.WARNING, message="Error occurred during copy: %s " % e)
            return redirect(reverse('admin:waves_service_change', args=[self.kwargs.get('service_id')]))


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
