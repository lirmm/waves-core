from django.conf.urls import url, include
from rest_framework import routers

from waves.api.v1.views import jobs, services
from waves.core.views import JobOutputView, JobInputView

app_name = "waves.api.v1"
# API router setup
router = routers.DefaultRouter()
# Services URIs configuration
router.register(prefix=r'services',
                viewset=services.ServiceViewSet,
                basename='waves-services')
# Jobs URIs configuration
router.register(prefix=r'jobs',
                viewset=jobs.JobViewSet,
                basename='waves-jobs')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^services/(?P<service>[^/.]+)/submissions/(?P<api_name>[^/.]+)/$',
        services.ServiceJobSubmissionView.as_view(), name='waves-services-submissions'),
    url(r'^jobs/outputs/(?P<slug>[\w-]+)/$', JobOutputView.as_view(), name="waves-job-output"),
    url(r'^jobs/inputs/(?P<slug>[\w-]+)/$', JobInputView.as_view(), name="waves-job-input"),
]
