"""
Base Test class for Runner's adaptors
"""
from __future__ import unicode_literals

import logging
import os
import time

from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import localtime

from waves.adaptors.core.base import JobAdaptor
from waves.adaptors.exceptions.adaptors import AdaptorInitError
from waves.adaptors.mocks import MockJobRunnerAdaptor
from waves.exceptions.jobs import *
from waves.models import *
from waves.tests.base import WavesBaseTestCase

logger = logging.getLogger(__name__)

__all__ = ['TestJobRunner', 'sample_runner']


def sample_runner(runner_impl):
    """
    Return a new adaptor model instance from adaptor class object
    Args:
        runner_impl: a JobRunnerAdaptor object
    Returns:
        Runner model instance
    """
    runner_model = Runner.objects.create(name=runner_impl.__class__.__name__,
                                         description='SubmissionSample Runner %s' % runner_impl.__class__.__name__,
                                         clazz='%s.%s' % (runner_impl.__module__, runner_impl.__class__.__name__))
    object_ctype = ContentType.objects.get_for_model(runner_model)
    for name, value in runner_impl.init_params.items():
        AdaptorInitParam.objects.update_or_create(name=name, content_type=object_ctype, object_id=runner_model.pk,
                                                  defaults={'default': value})
    return runner_model


def sample_job(service):
    """
    Return a new Job model instance for service
    Args:
        service: a Service model instance
    Returns:
        Job model instance
    """
    job = Job.objects.create(title='SubmissionSample Job', submission=service.submissions.first())
    srv_submission = service.default_submission
    for srv_input in srv_submission.submission_inputs.all():
        job.job_inputs.add(JobInput.objects.create(srv_input=srv_input, job=job, value="fake_value"))
    return job


def sample_service(runner, init_params=None):
    """ Create a sample service for this runner """
    service = Service.objects.create(name='Sample Service', runner=runner)
    if init_params:
        for name, value in init_params:
            service.run_params.add(ServiceRunParam.objects.create(name=name, value=value))
    sub = Submission.objects.create(name="Default Submission", service=service)
    service.submissions.add(sub)

    return service


class TestJobRunner(WavesBaseTestCase):
    """
    Test all functions in Runner adapters base class

    """

    def testLoadModules(self):
        from waves.addons.loader import load_core, load_extra_adaptors #, load_extra_importers
        cores = load_core()
        addons = load_extra_adaptors()
        # importers = load_extra_importers()

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
        # if not waves.settings.WAVES_TEST_DEBUG:
        #    for job in self.jobs:
        #        job.delete_job_dirs()

    def testConnect(self):
        # Only run for sub classes
        self.adaptor.connect()
        self.assertTrue(self.adaptor.connected)
        self.assertIsNotNone(self.adaptor._connector)
        self.adaptor.disconnect()
        self.assertFalse(self.adaptor.connected)

    def testWrongJobStates(self):
        """ Test exceptions raise when state inconsistency is detected in jobs
        """
        if not self.__class__.__name__ == 'TestJobRunner':
            self.skipTest("Only run with mock adaptor, just check job states consistency")
        self.current_job = sample_job(self.service)

        with self.assertRaises(AdaptorInitError):
            self.adaptor = JobAdaptor(init_params=dict(unexpected_param='unexpected value'))

        self.jobs.append(self.current_job)
        self._debug_job_state()
        self.current_job.status = Job.JOB_RUNNING
        length1 = self.current_job.job_history.count()
        logger.debug('Test Prepare')
        self._debug_job_state()
        with self.assertRaises(JobInconsistentStateError):
            self.current_job.run_prepare()
        self._debug_job_state()
        logger.debug('Test Run')
        self.current_job.status = Job.JOB_UNDEFINED
        with self.assertRaises(JobInconsistentStateError):
            self.current_job.run_launch()
        self._debug_job_state()
        logger.debug('Test Cancel')
        self.current_job.status = Job.JOB_COMPLETED
        with self.assertRaises(JobInconsistentStateError):
            self.current_job.run_cancel()
            # self.adaptor.cancel_job(self.current_job)
        logger.debug('Internal state %s, current %s', self.current_job._status, self.current_job.status)
        # status hasn't changed
        self.assertEqual(self.current_job.status, Job.JOB_COMPLETED)
        logger.debug('%i => %s', len(self.current_job.job_history.values()), self.current_job.job_history.values())
        # assert that no history element has been added
        self.assertEqual(length1, self.current_job.job_history.count())
        self.current_job.status = Job.JOB_RUNNING
        self.current_job.run_cancel()
        self.assertTrue(self.current_job.status == Job.JOB_CANCELLED)

    def runJobWorkflow(self, job=None):
        if job is not None:
            self.current_job = job
        if self.current_job is None:
            self.current_job = sample_job(self.service)
        if self.current_job not in self.jobs:
            self.jobs.append(self.current_job)
        assert isinstance(self.current_job, Job)
        logger.info('Starting workflow process for job %s', self.current_job)
        self.assertGreaterEqual(self.current_job.job_history.count(), 1)
        # self.adaptor.prepare_job(self.current_job)
        self.current_job.run_prepare()
        self.assertEqual(self.current_job.status, Job.JOB_PREPARED)
        self.current_job.run_launch()
        logger.debug('Remote Job ID %s', self.current_job.remote_job_id)
        self.assertEqual(self.current_job.status, Job.JOB_QUEUED)
        for ix in range(100):
            # job_state = self.adaptor.job_status(self.current_job)
            job_state = self.current_job.run_status()
            logger.info(u'Current job state (%i) : %s ', ix, self.current_job.get_status_display())
            if job_state >= Job.JOB_COMPLETED:
                logger.info('Job state ended to %s ', self.current_job.get_status_display())
                break
            else:
                time.sleep(3)
        if self.current_job.status in (Job.JOB_COMPLETED, Job.JOB_TERMINATED):
            # Get job run details
            # self.adaptor.job_run_details(self.current_job)
            self.current_job.run_details()
            history = self.current_job.job_history.first()
            logger.debug("History timestamp %s", localtime(history.timestamp))
            logger.debug("Job status timestamp %s", self.current_job.status_time)
            self.assertTrue(self.current_job.results_available)
            for output_job in self.current_job.outputs.all():
                # TODO reactivate job output verification as soon as possible
                if not os.path.isfile(output_job.file_path):
                    logger.warning("Job <<%s>> did not output expected %s (test_data/jobs/%s/) ",
                                   self.current_job.title, output_job.value, self.current_job.slug)

                self.assertTrue(os.path.isfile(output_job.file_path),
                                msg="Job <<%s>> did not output expected %s (test_data/jobs/%s/) " %
                                    (self.current_job.title, output_job.value, self.current_job.slug))
                logger.info("Expected output file: %s ", output_job.file_path)
            self.assertGreaterEqual(self.current_job.status, Job.JOB_COMPLETED)
        else:
            logger.warn('problem with job status %s', self.current_job.get_status_display())
        return True
