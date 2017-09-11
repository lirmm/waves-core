from __future__ import unicode_literals

from uuid import UUID

import swapper
from django.contrib import messages
from django.urls import reverse
from django.views import generic

from waves.wcore.exceptions.jobs import JobException
from waves.wcore.forms.services import ServiceSubmissionForm
from waves.wcore.models.jobs import Job
from waves.wcore.models.services import Submission

Service = swapper.load_model("wcore", "Service")


class ServiceModalPreview(generic.DetailView):
    model = Service
    context_object_name = 'service'
    queryset = Service.objects.all().prefetch_related('submissions')
    object = None
    template_name = 'admin/waves/service/service_preview.html'


class SubmissionFormView(generic.FormView, generic.DetailView):
    model = Service
    context_object_name = 'service'
    queryset = Service.objects.all().prefetch_related('submissions')
    object = None
    template_name = 'admin/waves/service/service_modal.html'
    form_class = ServiceSubmissionForm
    view_mode = ''

    def __init__(self, **kwargs):
        super(SubmissionFormView, self).__init__(**kwargs)

    def get_submissions(self):
        return self.get_object().submissions

    def get_success_url(self):
        return reverse('wcore:submission', kwargs={'pk': self.get_object().id})

    def _get_selected_submission(self):
        slug = self.request.POST.get('slug', None)
        if slug is None:
            return self.get_object().default_submission
        else:
            return Submission.objects.get(slug=UUID(slug))

    def get_context_data(self, **kwargs):
        if 'form' not in kwargs:
            kwargs.update({'form': []})
            form = None
        else:
            form = kwargs['form']
        # self.object = self.get_object()
        context = super(SubmissionFormView, self).get_context_data(**kwargs)
        context['selected_submission'] = self._get_selected_submission()
        context['submissions'] = []
        for submission in self.get_submissions().all():
            if form is not None and str(submission.slug) == form.cleaned_data['slug']:
                context['submissions'].append({'submission': submission, 'form': form})
            else:
                context['submissions'].append(
                    {'submission': submission, 'form': self.form_class(instance=submission, parent=self.object,
                                                                       user=self.request.user)})
        return context

    def get_form_kwargs(self):
        kwargs = super(SubmissionFormView, self).get_form_kwargs()
        extra_kwargs = {
            'parent': self.object,
        }
        extra_kwargs.update(kwargs)
        return extra_kwargs

    def post(self, request, *args, **kwargs):
        form = ServiceSubmissionForm(parent=self.get_object(),
                                     instance=self._get_selected_submission(),
                                     data=self.request.POST,
                                     files=self.request.FILES)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(**{'form': form})

    def form_valid(self, form):
        # create job in database
        ass_email = form.cleaned_data.pop('email')
        if not ass_email and self.request.user.is_authenticated():
            ass_email = self.request.user.email
        user = self.request.user if self.request.user.is_authenticated() else None
        try:
            job = Job.objects.create_from_submission(submission=self.selected_submission,
                                                     email_to=ass_email,
                                                     submitted_inputs=form.cleaned_data,
                                                     user=user)
            messages.success(
                self.request,
                "Job successfully submitted %s" % job.slug
            )
        except JobException as e:
            messages.error(
                self.request,
                "An unexpected error occurred, sorry for the inconvenience, our team has been noticed"
            )
            return self.render_to_response(self.get_context_data(form=form))
        return super(SubmissionFormView, self).form_valid(form)

    def form_invalid(self, **kwargs):
        messages.error(
            self.request,
            "Your job could not be submitted, check errors"
        )
        return self.render_to_response(self.get_context_data(**kwargs))
