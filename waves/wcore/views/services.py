from __future__ import unicode_literals

from uuid import UUID
import logging

from django.contrib import messages
from django.db import transaction
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse
from django.views import generic
from django.core.exceptions import PermissionDenied

from waves.wcore.exceptions.jobs import JobException
from waves.wcore.forms.services import ServiceSubmissionForm
from waves.wcore.models import Job, get_submission_model, get_service_model
from waves.wcore.settings import waves_settings

Submission = get_submission_model()
Service = get_service_model()
logger = logging.getLogger(__name__)

class SubmissionFormView(generic.FormView, generic.DetailView):
    model = Service
    context_object_name = 'service'
    queryset = Service.objects.all().prefetch_related('submissions')
    object = None
    # template_name = 'waves/services/bootstrap/submission_form.html'
    form_class = ServiceSubmissionForm
    view_mode = ''
    job = None

    def get_template_names(self):
        if self.template_name is None:
            self.template_name = 'waves/services/' + waves_settings.TEMPLATE_PACK + '/submission_form.html'
        try:
            get_template('waves/override/submission_' + self.get_object().api_name + '_form.html')
            return ['waves/override/submission_' + self.get_object().api_name + '_form.html']
        except TemplateDoesNotExist:
            pass
        return super(SubmissionFormView, self).get_template_names()

    def __init__(self, **kwargs):
        super(SubmissionFormView, self).__init__(**kwargs)

    def get_submissions(self):
        submissions = self.get_object().submissions
        available = []
        for submission in submissions.all():
            available.append(submission) if submission.available_for_user(self.request.user) else None
        if len(available) == 0:
            raise PermissionDenied()
        return available

    def get_object(self, queryset=None):
        self.object = super(SubmissionFormView, self).get_object(queryset)
        return self.object

    def get_success_url(self):
        if 'preview' in self.request.path:
            return self.request.path
        return reverse('wcore:job_details', kwargs={'unique_id': self.job.slug})

    def _get_selected_submission(self):
        slug = self.request.POST.get('slug', None)
        if slug is None:
            return self.get_object().default_submission
        else:
            return Submission.objects.get(slug=UUID(slug))

    def get_context_data(self, **kwargs):
        form = kwargs.get('form', {'form': []})
        #if 'form' not in kwargs:
        #    kwargs.update({'form': []})
        #    form = None
        #else:
        #    form = kwargs['form']
        # self.object = self.get_object()
        context = super(SubmissionFormView, self).get_context_data(**kwargs)
        context['submissions'] = []
        submissions = self.get_submissions()
        context['selected_submission'] = self._get_selected_submission()
        for submission in submissions:

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
            'request': self.request
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

    @transaction.atomic
    def form_valid(self, form):
        # create job in database
        ass_email = form.cleaned_data.pop('email')
        if not ass_email and self.request.user.is_authenticated():
            ass_email = self.request.user.email
        user = self.request.user if self.request.user.is_authenticated() else None
        try:
            self.job = Job.objects.create_from_submission(submission=self._get_selected_submission(),
                                                          email_to=ass_email,
                                                          submitted_inputs=form.cleaned_data,
                                                          user=user)
            messages.success(
                self.request,
                "Job successfully submitted %s" % self.job.slug
            )
        except JobException as e:
            logger.exception("JobException %s: %s", self.job.id, e.message)
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


class ServiceListView(generic.ListView):
    template_name = "waves/services/services_list.html"
    model = Service
    context_object_name = 'available_services'

    def get_queryset(self):
        return Service.objects.get_services(self.request.user).prefetch_related('submissions')


class ServiceDetailView(generic.DetailView):
    model = Service
    template_name = 'waves/services/service_details.html'
    context_object_name = 'service'
    queryset = Service.objects.all().prefetch_related('submissions')
    object = None
    slug_field = 'api_name'
    slug_url_kwarg = 'service_app_name'

    def get_context_data(self, **kwargs):
        context = super(ServiceDetailView, self).get_context_data(**kwargs)
        return context

    def get_object(self, queryset=None):
        obj = super(ServiceDetailView, self).get_object(queryset)
        self.object = obj
        if not obj.available_for_user(self.request.user):
            raise PermissionDenied()
        return obj

    def get_template_names(self):
        try:
            get_template(
                'waves/override/service_' + self.get_object().api_name + '_' + self.get_object().version +
                '_details.html')
            return [
                'waves/override/service_' + self.get_object().api_name + '_' + self.get_object().version +
                '_details.html']
        except TemplateDoesNotExist:
            try:
                get_template('waves/override/service_' + self.get_object().api_name + '_details.html')
                return ['waves/override/service_' + self.get_object().api_name + '_details.html']
            except TemplateDoesNotExist:
                return ['waves/services/service_details.html']
