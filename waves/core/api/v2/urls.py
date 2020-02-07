from __future__ import unicode_literals

from django.conf.urls import url, include
from rest_framework import routers

from waves.core.api.v2.views import jobs, services

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

urlpatterns = [
    url(r'^', include(router.urls)),
]
