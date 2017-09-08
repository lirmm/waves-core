from uuid import UUID

import swapper
from django.views import generic

from waves.wcore.forms.services import ServiceSubmissionForm
from waves.wcore.models import Submission

Service = swapper.load_model("wcore", "Service")


class JobSubmissionView(generic.FormView):
    model = Service
    template_name = 'waves/api/service_api_form.html'
    form_class = ServiceSubmissionForm

    def __init__(self, *args, **kwargs):
        super(JobSubmissionView, self).__init__(*args, **kwargs)
        self.user = None
        self.selected_submission = None

    def get(self, request, *args, **kwargs):
        self.user = self.request.user
        self.selected_submission = self._get_selected_submission()
        return super(JobSubmissionView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        if 'form' not in kwargs:
            kwargs.update({'form': []})
            form = None
        else:
            form = kwargs['form']
        # self.object = self.get_object()
        context = super(JobSubmissionView, self).get_context_data(**kwargs)
        context['selected_submission'] = self._get_selected_submission()
        context['forms'] = []
        for submission in self.get_object().submissions.all():
            if form is not None and str(submission.slug) == form.cleaned_data['slug']:
                context['forms'].append(form)
            else:
                context['forms'].append(self.form_class(instance=submission, parent=self.object,
                                                        user=self.request.user))
        return context

    def get_form(self, form_class=None):
        return super(JobSubmissionView, self).get_form(form_class)

    def get_form_kwargs(self):
        kwargs = super(JobSubmissionView, self).get_form_kwargs()
        extra_kwargs = {
            'parent': self.object,
        }
        extra_kwargs.update(kwargs)
        return extra_kwargs

    def _get_selected_submission(self):
        slug = self.request.POST.get('slug', None)
        if slug is None:
            return self.get_object().default_submission  # Submission.objects.get(default=True, service=)
        else:
            return Submission.objects.get(slug=UUID(slug))

    def post(self, request, *args, **kwargs):
        # DO nothing, because this view is only intended to display form
        pass


