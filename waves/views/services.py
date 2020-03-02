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
import logging
from uuid import UUID

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse
from django.views import generic

from waves.forms import frontend
from waves.core.exceptions import JobException
from waves.models import Job, Submission, Service
from waves.settings import waves_settings

logger = logging.getLogger(__name__)


class SubmissionFormView(generic.FormView, generic.DetailView):
    model = Service
    context_object_name = 'service'
    queryset = Service.objects.all().prefetch_related('submissions')
    object = None
    form_class = frontend.ServiceSubmissionForm
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
        if 'form' not in kwargs:
            kwargs.update({'form': []})
            form = None
        else:
            form = kwargs['form']
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
                    {'submission': submission,
                     'form': frontend.ServiceSubmissionForm(instance=submission, parent=self.object,
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
        form = frontend.ServiceSubmissionForm(parent=self.get_object(),
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
        if not ass_email and self.request.user.is_authenticated:
            ass_email = self.request.user.email
        user = self.request.user if self.request.user.is_authenticated else None
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
            logger.exception("JobException %s: %s", self.job.id, e)
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
