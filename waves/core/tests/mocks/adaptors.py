""" Mock Adapter class for tests purpose
"""


import datetime
import random
import string
import time

from waves.core.adaptors.adaptor import JobAdaptor
from waves.core.adaptors.const import JobStatus


class MockConnector(object):
    pass


class MockJobRunnerAdaptor(JobAdaptor):
    _states_map = {
        JobStatus.JOB_UNDEFINED: JobStatus.JOB_UNDEFINED,
        JobStatus.JOB_CREATED: JobStatus.JOB_CREATED,
        JobStatus.JOB_QUEUED: JobStatus.JOB_QUEUED,
        JobStatus.JOB_RUNNING: JobStatus.JOB_RUNNING,
        JobStatus.JOB_SUSPENDED: JobStatus.JOB_SUSPENDED,
        JobStatus.JOB_CANCELLED: JobStatus.JOB_CANCELLED,
        JobStatus.JOB_COMPLETED: JobStatus.JOB_COMPLETED,
        JobStatus.JOB_TERMINATED: JobStatus.JOB_TERMINATED,
        JobStatus.JOB_ERROR: JobStatus.JOB_ERROR,
    }

    def __init__(self, command=None, protocol='http', host="localhost", **kwargs):
        super(MockJobRunnerAdaptor, self).__init__('mock', protocol, host, **kwargs)

    def _job_status(self, job):
        time.sleep(2)
        if job.status == JobStatus.JOB_RUNNING:
            return JobStatus.JOB_COMPLETED
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
