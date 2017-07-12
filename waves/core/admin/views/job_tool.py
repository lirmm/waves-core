""" Job tool WAVES admin dedicated views """
from __future__ import unicode_literals

from django.views.generic import View
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from waves.core.exceptions import *
from waves.core.models import Job


class JobCancelView(View):
    """ View after cancel a job, if possible """
    def get(self, request, *args, **kwargs):
        """ Try to cancel specified job (in kwargs), redirect to current job page """
        try:
            job = get_object_or_404(Job, id=self.kwargs['job_id'])
            runner = job.adaptor
            runner.cancel_job(job)
            messages.add_message(request, level=messages.SUCCESS, message="Job cancelled")
        except WavesException as e:
            messages.add_message(request, level=messages.ERROR, message=e.message)
        return redirect(reverse('admin:waves_job_change', args=[self.kwargs['job_id']]))


class JobRerunView(View):

    def get(self, request, *args, **kwargs):
        job = get_object_or_404(Job, id=self.kwargs['job_id'])
        if job.allow_rerun:
            try:
                job.re_run()
                messages.success(request, message="Job '%s' successfully marked for re-run" % job.title)
            except WavesException as exc:
                messages.error(request, message="Error occured %s " % exc.message)
        else:
            messages.error(request, message="You can't rerun this job")
        return redirect(reverse('admin:waves_job_changelist'))
