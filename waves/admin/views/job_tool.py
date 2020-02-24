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

from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import View

from waves.core.const import JobStatus
from waves.core.exceptions import WavesException
from waves.models import Job

__all__ = ['JobCancelView', 'JobRerunView']


class JobCancelView(View):
    """ View after cancel a job, if possible """

    def get(self, request):
        """ Try to cancel specified job (in kwargs), redirect to current job page """
        try:
            job = get_object_or_404(Job, id=self.kwargs['job_id'])
            runner = job.adaptor
            if runner is not None:
                runner.cancel_job(job)
            else:
                job.status = JobStatus.JOB_CANCELLED
                job.save()
            messages.add_message(request, level=messages.SUCCESS, message="Job cancelled")
        except WavesException as e:
            messages.add_message(request, level=messages.ERROR, message=e)
        return redirect(reverse('admin:wcore_job_change', args=[self.kwargs['job_id']]))


class JobRerunView(View):
    def get(self, request):
        job = get_object_or_404(Job, id=self.kwargs['job_id'])
        if job.allow_rerun:
            try:
                job.re_run()
                messages.success(request, message="Job '%s' successfully marked for re-run" % job.title)
            except WavesException as exc:
                messages.error(request, message="Error occurred %s " % exc)
        else:
            messages.error(request, message="You can't rerun this job")
        return redirect(reverse('admin:wcore_job_changelist'))
