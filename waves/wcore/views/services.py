from __future__ import unicode_literals

import swapper

from waves.front.views import ServiceDetailView

Service = swapper.load_model("wcore", "Service")


class SubmissionPreview(ServiceDetailView):
    template_name = 'admin/waves/service/service_preview.html'

    def get_context_data(self, **kwargs):
        context = super(SubmissionPreview, self).get_context_data(**kwargs)
        context['preview'] = True
        context['service_id'] = self.get_object().id
        return context
