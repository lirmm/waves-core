from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required

from waves.wcore.admin.views import *
from waves.wcore.views.services import *

# TODO change auth decorators to specific WAVES ones
urlpatterns = [
    url(r'^service/(?P<service_id>\d+)/import$', staff_member_required(ServiceParamImportView.as_view()),
        name="service_import_form"),
    url(r'^runner/(?P<runner_id>\d+)/import$', staff_member_required(RunnerImportToolView.as_view()),
        name="runner_import_form"),
    url(r'^service/(?P<service_id>\d+)/duplicate$', staff_member_required(ServiceDuplicateView.as_view()),
        name="service_duplicate"),
    url(r'^job/(?P<job_id>[0-9]+)/cancel/$', staff_member_required(JobCancelView.as_view()),
        name='job_cancel'),
    url(r'^job/(?P<job_id>[0-9]+)/rerun/$', staff_member_required(JobRerunView.as_view()),
        name='job_rerun'),
    url(r'^service/(?P<pk>\d+)/export$', staff_member_required(ServiceExportView.as_view()),
        name="service_export_form"),
    url(r'^service/(?P<pk>\d+)/check$', staff_member_required(ServiceTestConnectionView.as_view()),
        name="service_test_connection"),
    url(r'^runner/(?P<pk>\d+)/export$', staff_member_required(RunnerExportView.as_view()),
        name="runner_export_form"),
    url(r'^runner/(?P<pk>\d+)/check$', staff_member_required(RunnerTestConnectionView.as_view()),
        name="runner_test_connection"),
    url(r'^service/form/(?P<pk>\d+)/preview$', staff_member_required(SubmissionPreview.as_view()),
        name="service_submission_preview"),
]
