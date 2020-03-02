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
from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from waves.views import JobInputView, JobOutputView, JobSubmissionView, JobView, JobListView
from waves.views import ServiceListView, ServiceDetailView

app_name = "waves"

urlpatterns = [
    url(r'^services/$', ServiceListView.as_view(), name='services_list'),
    url(r'^service/(?P<service_app_name>[\w_-]+)/$', ServiceDetailView.as_view(), name='service_details'),
    url(r'^service/(?P<service_app_name>[\w_-]+)/new$', JobSubmissionView.as_view(), name='job_submission'),
    url(r'^jobs/(?P<unique_id>[\w-]+)/$', JobView.as_view(), name="job_details"),
    url(r'^jobs/inputs/(?P<slug>[\w-]+)/$', JobInputView.as_view(), name="job_input"),
    url(r'^jobs/outputs/(?P<slug>[\w-]+)/$', JobOutputView.as_view(), name="job_output"),
    url(r'^jobs/', login_required(JobListView.as_view()), name="job_list"),
]
