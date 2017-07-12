from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required

from waves.core.admin.views import *
from waves.core.views.jobs import *
from waves.core.views.services import *

# TODO change auth decorators to specific WAVES ones
waves_admin_url = [
    url(r'^admin/service/(?P<service_id>\d+)/import$', staff_member_required(ServiceParamImportView.as_view()),
        name="service_import_form"),
    url(r'^admin/runner/(?P<runner_id>\d+)/import$', staff_member_required(RunnerImportToolView.as_view()),
        name="runner_import_form"),
    url(r'^admin/service/(?P<service_id>\d+)/duplicate$', staff_member_required(ServiceDuplicateView.as_view()),
        name="service_duplicate"),
    url(r'^admin/job/(?P<job_id>[0-9]+)/cancel/$', staff_member_required(JobCancelView.as_view()),
        name='job_cancel'),
    url(r'^admin/job/(?P<job_id>[0-9]+)/rerun/$', staff_member_required(JobRerunView.as_view()),
        name='job_rerun'),
    url(r'^admin/service/(?P<pk>\d+)/export$', staff_member_required(ServiceExportView.as_view()),
        name="service_export_form"),
    url(r'^admin/service/(?P<pk>\d+)/check$', staff_member_required(ServiceTestConnectionView.as_view()),
        name="service_test_connection"),
    url(r'^admin/runner/(?P<pk>\d+)/export$', staff_member_required(RunnerExportView.as_view()),
        name="runner_export_form"),
    url(r'^admin/runner/(?P<pk>\d+)/check$', staff_member_required(RunnerTestConnectionView.as_view()),
        name="runner_test_connection"),
    url(r'^admin/service/form/(?P<pk>\d+)/preview$', staff_member_required(SubmissionPreview.as_view()),
        name="service_submission_preview"),
]
waves_front_url = [
    url(r'^services/$', ServiceListView.as_view(), name='services_list'),
    url(r'^service/(?P<pk>[0-9]+)/$', ServiceDetailView.as_view(), name='service_details'),
    url(r'^service/(?P<pk>[0-9]+)/create$', JobSubmissionView.as_view(), name='job_submission'),
    url(r'^jobs/(?P<slug>[\w-]+)/$', JobView.as_view(), name="job_details"),
    url(r'^jobs/inputs/(?P<slug>[\w-]+)/$', login_required(JobInputView.as_view()), name="job_input"),
    url(r'^jobs/outputs/(?P<slug>[\w-]+)/$', login_required(JobOutputView.as_view()), name="job_output"),
    url(r'^jobs/$', login_required(JobListView.as_view()), name="job_list"),
]


waves_api_url = [
    url(r'^api/v1/', include('waves.core.api.v1.urls', namespace='api_v1')),
    url(r'^api/', include('waves.core.api.v2.urls', namespace='api_v2')),
]

urlpatterns = waves_admin_url + waves_api_url + waves_front_url
