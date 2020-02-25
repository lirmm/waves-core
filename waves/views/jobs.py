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

from uuid import UUID

from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse
from django.views import generic

from waves.forms import frontend
from waves.models import JobOutput, JobInput, Job, Submission, Service
from .files import DownloadFileView
from .services import SubmissionFormView, ServiceDetailView


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
    form_class = frontend.ServiceSubmissionForm
    slug_field = 'api_name'
    slug_url_kwarg = 'service_app_name'

    def __init__(self, **kwargs):
        super(JobSubmissionView, self).__init__(**kwargs)
        self.job = None

    def get(self, request, *args, **kwargs):
        return super(JobSubmissionView, self).get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('wcore:job_details', kwargs={'unique_id': self.job.slug})

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
    slug_url_kwarg = "unique_id"
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
