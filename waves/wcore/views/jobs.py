""" WAVES jobs related web views """
from __future__ import unicode_literals

from uuid import UUID

from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.views import generic

from waves.wcore.forms.services import ServiceSubmissionForm

from waves.wcore.models import JobOutput, JobInput, Job, get_submission_model, get_service_model
from waves.wcore.views.files import DownloadFileView
from waves.wcore.views.services import SubmissionFormView, ServiceDetailView

Service = get_service_model()
Submission = get_submission_model()


class JobFileView(DownloadFileView):
    """ Extended FileView for job files """

    @property
    def file_description(self):
        raise NotImplementedError()

    context_object_name = "file_obj"

    @property
    def file_name(self):
        return self.object.value

    @property
    def file_path(self):
        return self.object.file_path

    @property
    def return_link(self):
        return self.object.job.get_absolute_url()


class JobOutputView(JobFileView):
    """ Extended JobFileView for job outputs """
    model = JobOutput

    @property
    def file_description(self):
        return self.object.name


class JobInputView(JobFileView):
    """ Extended JobFileView for job inputs """
    model = JobInput

    @property
    def file_description(self):
        return ""


class JobSubmissionView(ServiceDetailView, SubmissionFormView):
    model = Service
    template_name = 'waves/services/service_form.html'
    form_class = ServiceSubmissionForm
    slug_field = 'api_name'

    def get_template_names(self):
        return super(JobSubmissionView, self).get_template_names()

    def __init__(self, **kwargs):
        super(JobSubmissionView, self).__init__(**kwargs)
        self.job = None

    def get(self, request, *args, **kwargs):
        return super(JobSubmissionView, self).get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('wcore:job_details', kwargs={'slug': self.job.slug})

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