

from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from waves.core.views.jobs import JobInputView, JobOutputView, JobSubmissionView, JobView, JobListView
from waves.core.views.services import ServiceListView, ServiceDetailView
app_name = "waves.core"

urlpatterns = [
    url(r'^services/$', ServiceListView.as_view(), name='services_list'),
    url(r'^service/(?P<service_app_name>[\w_-]+)/$', ServiceDetailView.as_view(), name='service_details'),
    url(r'^service/(?P<service_app_name>[\w_-]+)/new$', JobSubmissionView.as_view(), name='job_submission'),
    url(r'^jobs/(?P<unique_id>[\w-]+)/$', JobView.as_view(), name="job_details"),
    url(r'^jobs/inputs/(?P<slug>[\w-]+)/$', JobInputView.as_view(), name="job_input"),
    url(r'^jobs/outputs/(?P<slug>[\w-]+)/$', JobOutputView.as_view(), name="job_output"),
    url(r'^jobs/', login_required(JobListView.as_view()), name="job_list"),
]
