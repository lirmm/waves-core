from __future__ import unicode_literals

import logging
import os
import unittest

import waves.wcore.adaptors.const
import waves.wcore.adaptors.test_settings
from waves.wcore.adaptors.cluster import SshClusterAdaptor
from waves.wcore.adaptors.exceptions import AdaptorException, AdaptorNotAvailableException
from waves.wcore.adaptors.mocks import MockJobRunnerAdaptor
from waves.wcore.adaptors.shell import LocalShellAdaptor, SshShellAdaptor, SshKeyShellAdaptor
from waves.wcore.exceptions.jobs import JobInconsistentStateError
from waves.wcore.settings import waves_settings
from waves.wcore.tests.base import BaseTestCase, TestJobWorkflowMixin
from waves.wcore.utils.encrypt import Encrypt
from .loader import AdaptorLoader

logger = logging.getLogger(__name__)

NO_CLUSTER_MESSAGE = "A valid local SGE cluster is needed to run this tests"
MISSING_TOOL_MESSAGE = "Executable script is not in PATH : %s"


def skip_unless_sge():
    if not any(os.path.islink(os.path.join(_, 'qsub')) for _ in os.environ['PATH'].split(os.pathsep)):
        return unittest.skip(NO_CLUSTER_MESSAGE)
    return lambda f: f


class AdaptorTestCase(BaseTestCase, TestJobWorkflowMixin):
    loader = AdaptorLoader
    adaptors = [
        LocalShellAdaptor(command='cp'),
        SshShellAdaptor(protocol='ssh', command='cp', user_id=waves.wcore.adaptors.test_settings.WAVES_TEST_SSH_USER_ID,
                        password=Encrypt.encrypt(waves.wcore.adaptors.test_settings.WAVES_TEST_SSH_USER_PASS),
                        basedir=waves.wcore.adaptors.test_settings.WAVES_TEST_SSH_BASE_DIR,
                        host=waves.wcore.adaptors.test_settings.WAVES_TEST_SSH_HOST),
        SshClusterAdaptor(protocol='sge', command='cp',
                          queue=waves.wcore.adaptors.test_settings.WAVES_SSH_TEST_SGE_CELL,
                          user_id=waves.wcore.adaptors.test_settings.WAVES_TEST_SSH_USER_ID,
                          password=Encrypt.encrypt(waves.wcore.adaptors.test_settings.WAVES_TEST_SSH_USER_PASS),
                          basedir=waves.wcore.adaptors.test_settings.WAVES_SSH_TEST_SGE_BASE_DIR,
                          host=waves.wcore.adaptors.test_settings.WAVES_TEST_SSH_HOST),
        SshClusterAdaptor(protocol='slurm', command='cp',
                          queue=waves.wcore.adaptors.test_settings.WAVES_SLURM_TEST_SSH_QUEUE,
                          user_id=waves.wcore.adaptors.test_settings.WAVES_SLURM_TEST_SSH_USER_ID,
                          password=waves.wcore.adaptors.test_settings.WAVES_SLURM_TEST_SSH_USER_PASS,
                          basedir=waves.wcore.adaptors.test_settings.WAVES_SLURM_TEST_SSH_BASE_DIR,
                          host=waves.wcore.adaptors.test_settings.WAVES_SLURM_TEST_SSH_HOST),
        SshKeyShellAdaptor(command='cp', user_id=waves.wcore.adaptors.test_settings.WAVES_SSH_KEY_USER_ID,
                           password=Encrypt.encrypt(waves.wcore.adaptors.test_settings.WAVES_SSH_KEY_PASSPHRASE),
                           basedir=waves.wcore.adaptors.test_settings.WAVES_SSH_KEY_BASE_DIR,
                           host=waves.wcore.adaptors.test_settings.WAVES_SSH_KEY_HOST)
    ]

    def test_serialize(self):
        for adaptor in self.adaptors:
            logger.info("Testing serialization for %s ", adaptor.name)
            try:
                serialized = AdaptorLoader.serialize(adaptor)
                unserialized = AdaptorLoader.unserialize(serialized)
                self.assertEqual(adaptor.__class__, unserialized.__class__)
            except AdaptorException as e:
                pass
            else:
                logger.info("Adaptor not available for testing protocol %s " % adaptor.name)

    def test_protocol(self):
        for adaptor in self.adaptors:
            logger.info("Testing availability for %s ", adaptor.name)
            try:
                if adaptor.available:
                    logger.debug("Saga host %s, protocol %s", adaptor.saga_host, adaptor.host)
                    self.assertTrue(adaptor.saga_host.startswith(adaptor.protocol))
            except AdaptorException as e:
                pass
            else:
                logger.info("Adaptor not available for testing protocol %s " % adaptor.name)

    def test_loader(self):
        list_adaptors = self.loader.get_adaptors()
        self.assertTrue(all([clazz.__class__ in waves_settings.ADAPTORS_CLASSES for clazz in list_adaptors]))
        [logger.debug(c) for c in list_adaptors]

    def test_init(self):
        for adaptor in waves_settings.ADAPTORS_CLASSES:
            new_instance = self.loader.load(adaptor, host="localTestHost", protocol="httpTest", command="CommandTest")
            self.assertEqual(new_instance.host, "localTestHost")
            self.assertEqual(new_instance.command, "CommandTest")
            self.assertEqual(new_instance.protocol, "httpTest")

    def test_credentials(self):
        for adaptor in self.adaptors:
            logger.debug('Connecting to %s', adaptor.name)
            logger.debug('With init params %s', adaptor.init_params)
            try:
                if adaptor.available:
                    self.adaptor = adaptor
                    self.adaptor.connect()
                    self.assertTrue(self.adaptor.connected)
                    logger.debug('Connected to %s ', self.adaptor.connexion_string())
                    self.adaptor.disconnect()
            except AdaptorException as e:
                pass

    def test_local_cp_job(self):
        adaptor = self.adaptors[0]
        logger.debug('Connecting to %s', adaptor.name)
        job = self.create_cp_job(source_file=self.get_sample(),
                                 submission=self.create_random_service().default_submission)
        job.adaptor = adaptor
        logger.info('job command line %s ', job.command_line)
        self.run_job_workflow(job)

    def test_slurm_cp_job(self):
        adaptor = self.adaptors[3]
        logger.debug('Connecting to %s', adaptor.name)
        job = self.create_cp_job(source_file=self.get_sample(),
                                 submission=self.create_random_service().default_submission)
        job.adaptor = adaptor
        logger.info('job command line %s ', job.command_line)
        self.run_job_workflow(job)

    def test_all_cp_jobs(self):
        for adaptor in self.adaptors:
            try:
                logger.debug('Connecting to %s', adaptor.name)
                job = self.create_cp_job(source_file=self.get_sample(),
                                         submission=self.create_random_service().default_submission)
                adaptor.command = 'cp'
                job.adaptor = adaptor
                self.run_job_workflow(job)
            except AdaptorNotAvailableException as e:
                logger.info('Adaptor %s is not locally available', adaptor)
                logger.exception(e.message)

    def debug_job_state(self):
        logger.debug('Internal state %s, current %s', self.current_job._status, self.current_job.status)

    def test_job_states(self):
        """
        Test exceptions raise when state inconsistency is detected in jobs
        """
        self.service = self.sample_service()
        self.current_job = self.sample_job(self.service)
        self.adaptor = MockJobRunnerAdaptor(unexpected_param='unexpected value')
        self.jobs.append(self.current_job)
        self.debug_job_state()
        self.current_job.status = waves.wcore.adaptors.const.JOB_RUNNING
        logger.debug('Test Prepare')
        self.debug_job_state()
        with self.assertRaises(JobInconsistentStateError):
            self.current_job.run_prepare()

        self.debug_job_state()
        logger.debug('Test Run')
        self.current_job.status = waves.wcore.adaptors.const.JOB_UNDEFINED
        with self.assertRaises(JobInconsistentStateError):
            self.current_job.run_launch()
        self.debug_job_state()
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
