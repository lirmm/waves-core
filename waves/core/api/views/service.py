from __future__ import unicode_literals

from django.contrib.staticfiles.storage import staticfiles_storage

from waves.core.views.services import SubmissionFormView


class JobSubmissionView(SubmissionFormView):
    template_name = 'waves/api/service_api_form.html'

    def get_css(self):
        """ link to service css """
        return [
            self.request.build_absolute_uri(staticfiles_storage.url('waves/css/forms.css')), ]

    def get_js(self):
        """ link to service js"""
        return [
            self.request.build_absolute_uri(staticfiles_storage.url('waves/js/services.js')),
            self.request.build_absolute_uri(staticfiles_storage.url('waves/js/api_services.js')),
        ]

    def get_context_data(self, **kwargs):
        context = super(JobSubmissionView, self).get_context_data(**kwargs)
        context['css'] = self.get_css()
        context['js'] = self.get_js()
        return context
