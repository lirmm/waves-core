"""
Base Test class for Runner's adaptors
"""
from __future__ import unicode_literals

import logging

import waves.wcore.adaptors.const
from waves.wcore.adaptors.exceptions import *
from waves.wcore.adaptors.mocks import MockJobRunnerAdaptor
from waves.wcore.exceptions.jobs import *
from waves.wcore.models import get_service_model, get_submission_model
from waves.wcore.tests.base import WavesBaseTestCase
from waves.wcore.tests.utils import sample_runner, sample_job

Service = get_service_model()
Submission = get_submission_model()

logger = logging.getLogger(__name__)

__all__ = ['TestJobRunner']


class TestJobRunner(WavesBaseTestCase):
    """
    Test all functions in Runner adapters base class

    """

    def _debug_job_state(self):
        logger.debug('Internal state %s, current %s', self.current_job._status, self.current_job.status)

    def setUp(self):
        # Create sample data
        super(TestJobRunner, self).setUp()
        try:
            getattr(self, 'adaptor')
        except AttributeError:
            self.adaptor = MockJobRunnerAdaptor()
        self.runner_model = sample_runner(self.adaptor)
        self.service = Service.objects.create(name="SubmissionSample Service", runner=self.runner_model)
        self.service.submissions.add(Submission.objects.create(name='samplesub', service=self.service))
        self.current_job = None
        self.jobs = []
        self._result = self.defaultTestResult()

    def tearDown(self):
        super(TestJobRunner, self).tearDown()
        # if not waves.wcore.settings.WAVES_TEST_DEBUG:
        #    for job in self.jobs:
        #        job.delete_job_dirs()

    def testConnect(self):
        # Only run for sub classes
        self.adaptor.connect()
        self.assertTrue(self.adaptor.connected)
        self.assertIsNotNone(self.adaptor.connector)
        self.adaptor.disconnect()
        self.assertFalse(self.adaptor.connected)

    def testWrongJobStates(self):
        """ Test exceptions raise when state inconsistency is detected in jobs
        """
        if not self.__class__.__name__ == 'TestJobRunner':
            self.skipTest("Only run with mock adaptor, just check job states consistency")
        self.current_job = sample_job(self.service)
        self.adaptor = MockJobRunnerAdaptor(unexpected_param='unexpected value')
        self.jobs.append(self.current_job)
        self._debug_job_state()
        self.current_job.status = waves.wcore.adaptors.const.JOB_RUNNING
        length1 = self.current_job.job_history.count()
        logger.debug('Test Prepare')
        self._debug_job_state()
        with self.assertRaises(JobInconsistentStateError):
            self.current_job.run_prepare()
        self._debug_job_state()
        logger.debug('Test Run')
        self.current_job.status = waves.wcore.adaptors.const.JOB_UNDEFINED
        with self.assertRaises(JobInconsistentStateError):
            self.current_job.run_launch()
        self._debug_job_state()
        logger.debug('Test Cancel')
        self.current_job.status = waves.wcore.adaptors.const.JOB_COMPLETED
        with self.assertRaises(JobInconsistentStateError):
            self.current_job.run_cancel()
            # self.adaptor.cancel_job(self.current_job)
        logger.debug('Internal state %s, current %s', self.current_job._status, self.current_job.status)
        # status hasn't changed
        self.assertEqual(self.current_job.status, waves.wcore.adaptors.const.JOB_COMPLETED)
        logger.debug('%i => %s', len(self.current_job.job_history.values()), self.current_job.job_history.values())
        # assert that no history element has been added
        self.current_job.status = waves.wcore.adaptors.const.JOB_RUNNING
        self.current_job.run_cancel()
        self.assertTrue(self.current_job.status == waves.wcore.adaptors.const.JOB_CANCELLED)

