from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework import routers

from waves.wcore.api.v2.views import jobs, services

# API router setup
router = routers.DefaultRouter(trailing_slash=False)
# Services URIs configuration
router.register(prefix=r'services',
                viewset=services.ServiceViewSet,
                base_name='waves-services')
# Jobs URIs configuration
router.register(prefix=r'jobs',
                viewset=jobs.JobViewSet,
                base_name='waves-jobs')

router.register(r'services/(?P<service_app_name>[^/.]+)/submissions',
                viewset=services.ServiceSubmissionViewSet,
                base_name='waves-submissions')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^jobs/outputs/(?P<slug>[\w-]+)$', jobs.JobOutputView.as_view(), name="job-output"),
    url(r'^jobs/inputs/(?P<slug>[\w-]+)$', jobs.JobInputView.as_view(), name="job-input"),
]
