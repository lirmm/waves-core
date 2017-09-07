from __future__ import unicode_literals

import swapper
from django.views import generic
from django.urls import reverse

from waves.wcore.forms.services import ServiceSubmissionForm

Service = swapper.load_model("wcore", "Service")


class ServicePreview(generic.DetailView):
    model = Service
    context_object_name = 'service'
    queryset = Service.objects.all().prefetch_related('submissions')
    object = None
    template_name = 'admin/waves/service/service_preview.html'


class SubmissionPreview(generic.FormView, generic.DetailView):
    model = Service
    context_object_name = 'service'
    queryset = Service.objects.all().prefetch_related('submissions')
    object = None
    template_name = 'admin/waves/service/service_modal.html'
    form_class = ServiceSubmissionForm

    def get_success_url(self):
        return reverse('wcore:submission_preview', kwargs={'pk': self.get_object().id})

    def get_context_data(self, **kwargs):
        context = super(SubmissionPreview, self).get_context_data(**kwargs)
        context['preview'] = True
        context['service_id'] = self.get_object().id
        context['forms'] = []
        for submission in self.get_object().submissions.all():
            context['forms'].append(self.form_class(instance=submission, parent=self.object,
                                                    user=self.request.user))
        return context
