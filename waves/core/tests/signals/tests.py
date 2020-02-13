import logging
from os.path import isdir, join

from django.conf import settings
from django.test import TestCase, override_settings

from waves.core.models import JobStatus
from waves.core.tests.base import WavesTestCaseMixin
from waves.core.tests.mocks import SampleService

logger = logging.getLogger(__name__)


@override_settings(
    WAVES_CORE={
        'JOB_BASE_DIR': join(settings.BASE_DIR, 'tests', 'data', 'jobs'),
        'ADAPTORS_CLASSES': (
            'waves.tests.mocks.adaptors.MockJobRunnerAdaptor',
        )
    }
)
class SignalTestCase(TestCase, WavesTestCaseMixin):

    def testRunnerSignals(self):
        runner = None

    def testJobsSignals(self):
        service = SampleService()
        job = service.create_simple_job(self.api_user)
        self.assertIsNotNone(job.random_title)
        job.logger.debug("Test Debug Log message")
        self.assertTrue(isdir(job.working_dir))
        self.assertEqual(job.status, JobStatus.JOB_CREATED)
        self.assertEqual(job.job_history.count(), 1)
        job.message = "Test job Message"
        job.status = JobStatus.JOB_PREPARED
        job.save()
        self.assertEqual(job.job_history.filter(message=job.message).count(), 1)
        work_dir = job.working_dir
        job.delete()
        self.assertFalse(isdir(work_dir))
        logger.debug('Job directories has been deleted - job_post_delete_handler')
