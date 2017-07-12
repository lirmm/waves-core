""" Mock Adaptor class for tests purpose
"""
from __future__ import unicode_literals

import datetime
import random
import string
import time

import waves.core.adaptors.const
import waves.core.adaptors.utils
from waves.core.adaptors.adaptor import JobAdaptor


class MockConnector(object):
    pass


class MockJobRunnerAdaptor(JobAdaptor):
    _states_map = {
        waves.core.adaptors.const.JOB_UNDEFINED: waves.core.adaptors.const.JOB_UNDEFINED,
        waves.core.adaptors.const.JOB_CREATED: waves.core.adaptors.const.JOB_CREATED,
        waves.core.adaptors.const.JOB_QUEUED: waves.core.adaptors.const.JOB_QUEUED,
        waves.core.adaptors.const.JOB_RUNNING: waves.core.adaptors.const.JOB_RUNNING,
        waves.core.adaptors.const.JOB_SUSPENDED: waves.core.adaptors.const.JOB_SUSPENDED,
        waves.core.adaptors.const.JOB_CANCELLED: waves.core.adaptors.const.JOB_CANCELLED,
        waves.core.adaptors.const.JOB_COMPLETED: waves.core.adaptors.const.JOB_COMPLETED,
        waves.core.adaptors.const.JOB_TERMINATED: waves.core.adaptors.const.JOB_TERMINATED,
        waves.core.adaptors.const.JOB_ERROR: waves.core.adaptors.const.JOB_ERROR,
    }

    def __init__(self, command=None, protocol='http', host="localhost", **kwargs):
        super(MockJobRunnerAdaptor, self).__init__(command, protocol, host, **kwargs)
        self.command = 'mock_command'

    def _job_status(self, job):
        time.sleep(2)
        if job.status == waves.core.adaptors.const.JOB_RUNNING:
            # print "job is running, set it to completed!"
            return waves.core.adaptors.const.JOB_COMPLETED
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

    def _prepare_job(self, job):
        time.sleep(2)
        job.created = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%I')

    def _cancel_job(self, job):
        pass