from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required

from waves.admin.views import *
from waves.views.jobs import *
from waves.views.services import *

urlpatterns = [
    url(r'^services/$', CategoryListView.as_view(), name='services_list'),
    url(r'^category/(?P<pk>[0-9]+)/$', CategoryDetailView.as_view(), name='category_details'),
    url(r'^services/(?P<pk>[0-9]+)/$', ServiceDetailView.as_view(), name='service_details'),
    url(r'^services/(?P<pk>[0-9]+)/create$', JobSubmissionView.as_view(), name='job_submission'),
    # url(r'^unauthorized/$', HTML403.as_view(), name="unauthorized"),
    url(r'^jobs/(?P<slug>[\w-]+)/$', JobView.as_view(), name="job_details"),
    url(r'^jobs/inputs/(?P<slug>[\w-]+)/$', JobInputView.as_view(), name="job_input"),
    url(r'^jobs/outputs/(?P<slug>[\w-]+)/$', JobOutputView.as_view(), name="job_output"),
    url(r'^jobs/$', JobListView.as_view(), name="job_list"),
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
    url(r'^runner/(?P<pk>\d+)/export$', staff_member_required(RunnerExportView.as_view()),
        name="runner_export_form"),
    url(r'^runner/(?P<pk>\d+)/check$', staff_member_required(RunnerTestConnectionView.as_view()),
        name="runner_test_connection"),
    url(r'^service/(?P<pk>\d+)/check$', staff_member_required(ServiceTestConnectionView.as_view()),
        name="service_test_connection"),
]
