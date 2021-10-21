"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the GNU GPL v3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       https://www.gnu.org/licenses/gpl-3.0.en.html
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from django.urls import include, path, re_path
from rest_framework import routers

from waves.api.v1.views import jobs, services
from waves.views import JobOutputView, JobInputView

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
    path('', include(router.urls)),
    re_path(r'^services/(?P<service>[^/.]+)/submissions/(?P<api_name>[^/.]+)/$',
        services.ServiceJobSubmissionView.as_view(), name='waves-services-submissions'),
    re_path(r'^jobs/outputs/(?P<slug>[\w-]+)/$', JobOutputView.as_view(), name="waves-job-output"),
    re_path(r'^jobs/inputs/(?P<slug>[\w-]+)/$', JobInputView.as_view(), name="waves-job-input"),
]
