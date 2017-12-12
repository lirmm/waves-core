from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from waves.wcore.views.jobs import JobInputView, JobOutputView, JobSubmissionView, JobView, JobListView
from waves.wcore.views.services import ServiceListView, ServiceDetailView

# TODO change auth decorators to specific WAVES ones
urlpatterns = [
    url(r'^services/$', ServiceListView.as_view(), name='services_list'),
    url(r'^service/(?P<slug>[\w_-]+)/$', ServiceDetailView.as_view(), name='service_details'),
    url(r'^service/(?P<slug>[\w_-]+)/new', JobSubmissionView.as_view(), name='job_submission'),
    url(r'^jobs/(?P<slug>[\w-]+)/$', JobView.as_view(), name="job_details"),
    url(r'^jobs/inputs/(?P<slug>[\w-]+)/$', JobInputView.as_view(), name="job_input"),
    url(r'^jobs/outputs/(?P<slug>[\w-]+)/$', JobOutputView.as_view(), name="job_output"),
    url(r'^jobs/$', login_required(JobListView.as_view()), name="job_list"),
]
