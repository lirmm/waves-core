""" Job Utils functions """
from __future__ import unicode_literals


def default_run_details(job):
    """ Get and retriver a JobRunDetails namedtuple with defaults values"""
    from waves.adaptors.utils import JobRunDetails
    return JobRunDetails(job.id, str(job.slug), job.remote_job_id, job.title, job.exit_code,
                         job.created, '', '', '')
