import datetime
import random
import string
import time

from core.adaptors.base import JobAdaptor
from waves.core.models import *


class MockConnector:
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
        JobStatus.JOB_FINISHED: JobStatus.JOB_FINISHED,
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
        job.remote_job_id = '%s-%s' % (job.id, ''.join(random.sample(string.ascii_letters, 15)))
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
        time.sleep(2)
        job.status = JobStatus.JOB_CANCELLED


class SampleService:

    def __init__(self) -> None:
        super().__init__()
        adaptor = MockJobRunnerAdaptor()
        print("Names", adaptor.class_name)
        runner = Runner.objects.create(name="MockRunner",
                                       enabled=True,
                                       description="Mock Runner",
                                       short_description="Mock Runner",
                                       clazz=adaptor.class_name)
        self.service = Service.objects.create(name='Sample Service',
                                              runner=runner,
                                              status=Service.SRV_PUBLIC)
        print(self.service.default_submission)

    def simple_params(self):
        self.service.default_submission.inputs.add(
            TextParam.objects.create(name='TextInput',
                                     default='default',
                                     submission=self.service.default_submission))
        self.service.default_submission.inputs.add(
            BooleanParam.objects.create(name='BooleanParam',
                                        default=False,
                                        submission=self.service.default_submission))
        self.service.default_submission.inputs.add(
            FileInput.objects.create(name='FileInputParam',
                                     submission=self.service.default_submission))
        self.service.default_submission.outputs.add(
            SubmissionOutput.objects.create(submission=self.service.default_submission,
                                            label="Sample Output 1",
                                            extension="txt")
        )
        self.service.default_submission.outputs.add(
            SubmissionOutput.objects.create(submission=self.service.default_submission,
                                            label="Sample Output 2",
                                            extension="fasta")
        )

    def create_simple_job(self, user=None):
        job = Job.objects.create(submission=self.service.default_submission,
                                 client=user,
                                 email_to='waves@waves.com')
        for param in self.service.default_submission.inputs:
            job.job_inputs.add(JobInput.objects.create(name=f"Input_{param.name}",
                                                       value=f"Value_{param.name}",
                                                       job=job))
        for out in self.service.default_submission.outputs:
            job.outputs.add(JobOutput.objects.create(name=f"out {out.name}",
                                                     value=f"out value {out.name}",
                                                     job=job))
        return job
