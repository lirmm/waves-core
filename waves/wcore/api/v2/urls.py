from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework import routers

from waves.wcore.api.v2.views import jobs, services
from waves.wcore.views.jobs import JobOutputView, JobInputView

# API router setup
router = routers.DefaultRouter()
# Services URIs configuration
router.register(prefix=r'services',
                viewset=services.ServiceViewSet,
                base_name='waves-services')
# Jobs URIs configuration
router.register(prefix=r'jobs',
                viewset=jobs.JobViewSet,
                base_name='waves-jobs')

router.register(r'services/(?P<service>[^/.]+)/submissions',
                viewset=services.ServiceSubmissionViewSet,
                base_name='waves-submission')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'services/(?P<service>[^/.]+)/submissions/(?P<api_name>[^/.]+)/form',
        services.ServiceSubmissionViewSet.as_view({'get': 'submission_form'})),
    url(r'services/(?P<service>[^/.]+)/submissions/(?P<api_name>[^/.]+)',
        services.ServiceSubmissionViewSet.as_view({'post': 'create_job'})),
    url(r'^jobs/outputs/(?P<slug>[\w-]+)/$', JobOutputView.as_view(), name="waves-job-output"),
    url(r'^jobs/outputs/(?P<slug>[\w-]+)/raw$', jobs.JobOutputRawView.as_view(), name="waves-job-output-raw"),
    url(r'^jobs/inputs/(?P<slug>[\w-]+)/$', JobInputView.as_view(), name="waves-job-input"),
]
