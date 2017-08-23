from __future__ import unicode_literals

from uuid import UUID

import swapper
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.views import generic

from waves.wcore.exceptions.jobs import JobException
from waves.wcore.forms.services import ServiceSubmissionForm
from waves.wcore.models import Job
from waves.wcore.models.services import Submission

Service = swapper.load_model("wcore", "Service")


class ServiceListView(generic.ListView):
    template_name = "waves/services/services_list.html"
    model = Service
    context_object_name = 'available_services'

    def get_queryset(self):
        return Service.objects.all().prefetch_related('submissions')


class ServiceDetailView(generic.DetailView):
    model = Service
    template_name = 'waves/services/service_details.html'
    context_object_name = 'service'
    queryset = Service.objects.all().prefetch_related('submissions')
    object = None

    def get_context_data(self, **kwargs):
        context = super(ServiceDetailView, self).get_context_data(**kwargs)
        return context

    def get_object(self, queryset=None):
        obj = super(ServiceDetailView, self).get_object(queryset)
        self.object = obj
        if not obj.available_for_user(self.request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied()
        return obj


class JobSubmissionView(ServiceDetailView, generic.FormView):
    model = Service
    template_name = 'waves/services/service_form.html'
    form_class = ServiceSubmissionForm

    def get_template_names(self):
        return super(JobSubmissionView, self).get_template_names()

    def __init__(self, *args, **kwargs):
        super(JobSubmissionView, self).__init__(*args, **kwargs)
        self.job = None
        # self.object = None
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

    def get_success_url(self):
        return reverse('waves:job_details', kwargs={'slug': self.job.slug})

    def _get_selected_submission(self):
        slug = self.request.POST.get('slug', None)
        if slug is None:
            return self.get_object().default_submission  # Submission.objects.get(default=True, service=)
        else:
            submission = Submission.objects.get(slug=UUID(slug))
            return Submission.objects.get(slug=UUID(slug))

    def post(self, request, *args, **kwargs):
        self.user = self.request.user
        self.selected_submission = self._get_selected_submission()
        form = ServiceSubmissionForm(parent=self.get_object(),
                                     instance=self.selected_submission,
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
            self.job = Job.objects.create_from_submission(submission=self.selected_submission,
                                                          email_to=ass_email,
                                                          submitted_inputs=form.cleaned_data,
                                                          user=user)
            messages.success(
                self.request,
                "Job successfully submitted"
            )
        except JobException as e:
            messages.error(
                self.request,
                "An unexpected error occurred, sorry for the inconvenience, our team has been noticed"
            )
            return self.render_to_response(self.get_context_data(form=form))
        return super(JobSubmissionView, self).form_valid(form)

    def form_invalid(self, **kwargs):
        messages.error(
            self.request,
            "Your job could not be submitted, check errors"
        )
        return self.render_to_response(self.get_context_data(**kwargs))


class SubmissionPreview(ServiceDetailView):
    template_name = 'admin/waves/service/service_preview.html'

    def get_context_data(self, **kwargs):
        context = super(SubmissionPreview, self).get_context_data(**kwargs)
        context['preview'] = True
        context['service_id'] = self.get_object().id
        return context