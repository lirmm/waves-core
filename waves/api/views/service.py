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
from django.contrib.staticfiles.storage import staticfiles_storage

from waves.views import SubmissionFormView


class JobSubmissionView(SubmissionFormView):
    template_name = 'waves/api/service_api_form.html'

    def get_css(self):
        """ link to service css """
        return [
            self.request.build_absolute_uri(staticfiles_storage.url('waves/css/forms.css')), ]

    def get_js(self):
        """ link to service js"""
        return [
            self.request.build_absolute_uri(staticfiles_storage.url('waves/js/services.js')),
            self.request.build_absolute_uri(staticfiles_storage.url('waves/js/api_services.js')),
        ]

    def get_context_data(self, **kwargs):
        context = super(JobSubmissionView, self).get_context_data(**kwargs)
        context['css'] = self.get_css()
        context['js'] = self.get_js()
        return context
