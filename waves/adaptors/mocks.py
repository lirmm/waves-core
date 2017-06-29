""" Mock Adaptor class for tests purpose
"""
from __future__ import unicode_literals

import datetime
import random
import string
import time

import waves.adaptors.const
import waves.adaptors.core
import waves.adaptors.utils
from waves.adaptors.core.adaptor import JobAdaptor


class MockConnector(object):
    pass


class MockJobRunnerAdaptor(JobAdaptor):
    command = "fake"
    _states_map = {
        waves.adaptors.const.JOB_UNDEFINED: waves.adaptors.const.JOB_UNDEFINED,
        waves.adaptors.const.JOB_CREATED: waves.adaptors.const.JOB_CREATED,
        waves.adaptors.const.JOB_QUEUED: waves.adaptors.const.JOB_QUEUED,
        waves.adaptors.const.JOB_RUNNING: waves.adaptors.const.JOB_RUNNING,
        waves.adaptors.const.JOB_SUSPENDED: waves.adaptors.const.JOB_SUSPENDED,
        waves.adaptors.const.JOB_CANCELLED: waves.adaptors.const.JOB_CANCELLED,
        waves.adaptors.const.JOB_COMPLETED: waves.adaptors.const.JOB_COMPLETED,
        waves.adaptors.const.JOB_TERMINATED: waves.adaptors.const.JOB_TERMINATED,
        waves.adaptors.const.JOB_ERROR: waves.adaptors.const.JOB_ERROR,
    }

    def _job_status(self, job):
        time.sleep(2)
        if job.status == waves.adaptors.const.JOB_RUNNING:
            # print "job is running, set it to completed!"
            return waves.adaptors.const.JOB_COMPLETED
        job.updated = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%I')
        return job.next_status

    def _run_job(self, job):
        time.sleep(2)
        job.remote_job_id = '%s-%s' % (job.id, ''.join(random.sample(string.letters, 15)))
        job.started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%I')

    def _disconnect(self):
        self.connector = None
        pass

    def _connect(self):
        self.connector = MockConnector()
        self._connected = True
        pass

    def _job_results(self, job):
        time.sleep(2)
        return True

    def _job_run_details(self, job):
        return waves.adaptors.utils.JobRunDetails(job.id, str(job.slug), job.remote_job_id, job.title, job.exit_code,
                                                  job.created, job.started, job.updated, '')

    def _prepare_job(self, job):
        time.sleep(2)
        job.created = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%I')

    def _cancel_job(self, job):
        pass
