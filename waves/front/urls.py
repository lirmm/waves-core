from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from waves.front.views import ServiceListView, ServiceDetailView, JobSubmissionView, JobView, JobListView
from waves.wcore.views.jobs import JobInputView, JobOutputView

urlpatterns = [
    url(r'^services/$', ServiceListView.as_view(), name='services_list'),
    url(r'^service/(?P<pk>[0-9]+)/$', ServiceDetailView.as_view(), name='service_details'),
    url(r'^service/(?P<pk>[0-9]+)/create$', JobSubmissionView.as_view(), name='job_submission'),
    url(r'^jobs/(?P<slug>[\w-]+)/$', JobView.as_view(), name="job_details"),
    url(r'^jobs/inputs/(?P<slug>[\w-]+)/$', login_required(JobInputView.as_view()), name="job_input"),
    url(r'^jobs/outputs/(?P<slug>[\w-]+)/$', login_required(JobOutputView.as_view()), name="job_output"),
    url(r'^jobs/$', login_required(JobListView.as_view()), name="job_list"),
]