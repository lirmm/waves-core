from __future__ import unicode_literals

from uuid import UUID

from django.urls import reverse
from django.views import generic
from django.http import Http404
from django.template.loader import select_template, get_template
from django.template import TemplateDoesNotExist

from waves.wcore.forms.services import ServiceSubmissionForm
from waves.wcore.views.services import SubmissionFormView
from waves.wcore.models import get_service_model, Job, get_submission_model

Service = get_service_model()
Submission = get_submission_model()


class ServiceListView(generic.ListView):
    template_name = "waves/services/services_list.html"
    model = Service
    context_object_name = 'available_services'

    def get_queryset(self):
        return Service.objects.all().prefetch_related('submissions')


class ServiceDetailView(generic.DetailView):
    model = Service
    # template_name = 'waves/services/service_details.html'
    context_object_name = 'service'
    queryset = Service.objects.all().prefetch_related('submissions')
    object = None
    slug_field = 'api_name'

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

    def get_template_names(self):
        try:
            get_template(
                'waves/override/service_' + self.get_object().api_name + '_' + self.get_object().version + '_details.html')
            return [
                'waves/override/service_' + self.get_object().api_name + '_' + self.get_object().version + '_details.html']
        except TemplateDoesNotExist:
            try:
                get_template('waves/override/service_' + self.get_object().api_name + '_details.html')
                return ['waves/override/service_' + self.get_object().api_name + '_details.html']
            except TemplateDoesNotExist:
                return ['waves/services/service_details.html']


class JobSubmissionView(ServiceDetailView, SubmissionFormView):
    model = Service
    template_name = 'waves/services/service_form.html'
    form_class = ServiceSubmissionForm
    slug_field = 'api_name'

    def get_template_names(self):
        return super(JobSubmissionView, self).get_template_names()

    def get_submissions(self):
        return self.get_object().submissions_web

    def __init__(self, **kwargs):
        super(JobSubmissionView, self).__init__(**kwargs)
        self.job = None
        self.user = None
        self.selected_submission = None

    def get(self, request, *args, **kwargs):
        self.user = self.request.user
        self.selected_submission = self._get_selected_submission()
        return super(JobSubmissionView, self).get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('wfront:job_details', kwargs={'slug': self.job.slug})

    def _get_selected_submission(self):
        slug = self.request.POST.get('slug', None)
        if slug is None:
            return self.get_object().default_submission  # Submission.objects.get(default=True, service=)
        else:
            return Submission.objects.get(slug=UUID(slug))

    def get_template_names(self):
        try:
            get_template(
                'waves/override/service_' + self.get_object().api_name + '_' + self.get_object().version + '_form.html')
            return [
                'waves/override/service_' + self.get_object().api_name + '_' + self.get_object().version + '_form.html']
        except TemplateDoesNotExist:
            try:
                get_template('waves/override/service_' + self.get_object().api_name + '_form.html')
                return ['waves/override/service_' + self.get_object().api_name + '_form.html']
            except TemplateDoesNotExist:
                return ['waves/services/service_form.html']


class JobView(generic.DetailView):
    """ Job Detail view """
    model = Job
    slug_field = 'slug'
    template_name = 'waves/jobs/job_detail.html'
    context_object_name = 'job'


class JobListView(generic.ListView):
    """ Job List view (for user) """
    model = Job
    template_name = 'waves/jobs/job_list.html'
    context_object_name = 'job_list'
    paginate_by = 10

    def get_queryset(self):
        """ Retrieve user job """
        return Job.objects.get_user_job(user=self.request.user)
