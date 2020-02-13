import logging
import os
import unittest

from django.conf import settings

from waves.adaptors import SshClusterAdaptor
from waves.adaptors.const import JobStatus
from waves.adaptors import AdaptorException
from waves.adaptors import LocalShellAdaptor, SshShellAdaptor, SshKeyShellAdaptor
from waves.core.exceptions import JobInconsistentStateError
from waves.core.settings import waves_settings
from waves.core.tests.base import WavesTestCaseMixin, TestJobWorkflowMixin
from waves.core.tests.mocks import MockJobRunnerAdaptor
from waves.utils.encrypt import Encrypt
from waves.adaptors import AdaptorLoader

logger = logging.getLogger(__name__)

NO_CLUSTER_MESSAGE = "A valid local SGE cluster is needed to run this tests"
MISSING_TOOL_MESSAGE = "Executable script is not in PATH : %s"


def skip_unless_sge():
    if not any(os.path.islink(os.path.join(_, 'qsub')) for _ in os.environ['PATH'].split(os.pathsep)):
        return unittest.skip(NO_CLUSTER_MESSAGE)
    return lambda f: f


class AdaptorTestCase(WavesTestCaseMixin, TestJobWorkflowMixin):
    loader = AdaptorLoader
    adaptors = {"local": LocalShellAdaptor(command='cp')}

    def setUp(self):
        super(AdaptorTestCase, self).setUp()
        if hasattr(settings, "WAVES_TEST_SSH_USER_ID"):
            self.adaptors["sshShell"] = SshShellAdaptor(protocol='ssh', command='cp',
                                                        user_id=settings.WAVES_TEST_SSH_USER_ID,
                                                        password=Encrypt.encrypt(
                                                            settings.WAVES_TEST_SSH_USER_PASS),
                                                        basedir=settings.WAVES_TEST_SSH_BASE_DIR,
                                                        host=settings.WAVES_TEST_SSH_HOST)
        if hasattr(settings, "WAVES_TEST_SGE_CELL"):
            self.adaptors['localSge'] = SshClusterAdaptor(protocol='sge', command='cp',
                                                          queue=settings.WAVES_TEST_SGE_CELL,
                                                          basedir=settings.WAVES_TEST_SGE_BASE_DIR,
                                                          host="localhost")
        if hasattr(settings, "WAVES_SSH_TEST_SGE_CELL"):
            self.adaptors['sshSge'] = SshClusterAdaptor(protocol='sge', command='cp',
                                                        queue=settings.WAVES_SSH_TEST_SGE_CELL,
                                                        user_id=settings.WAVES_TEST_SSH_USER_ID,
                                                        password=Encrypt.encrypt(
                                                            settings.WAVES_TEST_SSH_USER_PASS),
                                                        basedir=settings.WAVES_SSH_TEST_SGE_BASE_DIR,
                                                        host=settings.WAVES_TEST_SSH_HOST)
        if hasattr(settings, "WAVES_SSH_KEY_USER_ID"):
            self.adaptors["sshShell"] = SshKeyShellAdaptor(command='cp', user_id=settings.WAVES_SSH_KEY_USER_ID,
                                                           password=Encrypt.encrypt(settings.WAVES_SSH_KEY_PASSPHRASE),
                                                           basedir=settings.WAVES_SSH_KEY_BASE_DIR,
                                                           host=settings.WAVES_SSH_KEY_HOST)
        if hasattr(settings, "WAVES_SLURM_TEST_SSH_QUEUE"):
            self.adaptors["sshSlurm"] = SshClusterAdaptor(protocol='slurm', command='cp',
                                                          queue=settings.WAVES_SLURM_TEST_SSH_QUEUE,
                                                          user_id=settings.WAVES_SLURM_TEST_SSH_USER_ID,
                                                          password=settings.WAVES_SLURM_TEST_SSH_USER_PASS,
                                                          basedir=settings.WAVES_SLURM_TEST_SSH_BASE_DIR,
                                                          host=settings.WAVES_SLURM_TEST_SSH_HOST)

    def test_serialize(self):
        for code, adaptor in self.adaptors.items():
            logger.info("Testing serialization for %s ", adaptor.name)
            try:
                serialized = AdaptorLoader.serialize(adaptor)
                unserialized = AdaptorLoader.unserialize(serialized)
                self.assertEqual(adaptor.__class__, unserialized.__class__)
            except AdaptorException as e:
                logger.exception("AdaptorException in %s: %s", adaptor.__class__.__name__, e.message)
                pass
            else:
                logger.info("Adaptor not available for testing protocol %s " % adaptor.name)

    def test_protocol(self):
        for code, adaptor in self.adaptors.items():
            logger.info("Testing availability for %s ", adaptor.name)
            try:
                if adaptor.available:
                    logger.debug("Saga host %s, protocol %s", adaptor.saga_host, adaptor.host)
                    self.assertTrue(adaptor.saga_host.startswith(adaptor.protocol))
            except AdaptorException as e:
                logger.exception("AdaptorException in %s: %s", adaptor.__class__.__name__, e.message)
                pass
            else:
                logger.info("Adaptor not available for testing protocol %s " % adaptor.name)

    def test_loader(self):
        list_adaptors = self.loader.get_adaptors()
        from waves.core.settings import waves_settings
        self.assertTrue(all([clazz.__class__ in waves_settings.ADAPTORS_CLASSES for clazz in list_adaptors]))
        [logger.debug(c) for c in list_adaptors]

    def test_init(self):
        for adaptor in waves_settings.ADAPTORS_CLASSES:
            new_instance = self.loader.load(adaptor, host="localTestHost", protocol="httpTest",
                                            command="CommandTest")
            self.assertEqual(new_instance.host, "localTestHost")
            self.assertEqual(new_instance.command, "CommandTest")
            self.assertEqual(new_instance.protocol, "httpTest")

    def test_credentials(self):
        for name, adaptor in self.adaptors.items():
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
                logger.warning("AdaptorException in %s: %s", adaptor.__class__.__name__, e.message)

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
        self.current_job.status = JobStatus.JOB_RUNNING
        logger.debug('Test Prepare')
        self.debug_job_state()
        with self.assertRaises(JobInconsistentStateError):
            self.current_job.run_prepare()

        self.debug_job_state()
        logger.debug('Test Run')
        self.current_job.status = JobStatus.JOB_UNDEFINED
        with self.assertRaises(JobInconsistentStateError):
            self.current_job.run_launch()
        self.debug_job_state()
        logger.debug('Test Cancel')
        self.current_job.status = JobStatus.JOB_COMPLETED
        with self.assertRaises(JobInconsistentStateError):
            self.current_job.run_cancel()
            # self.adaptor.cancel_job(self.current_job)
        logger.debug('Internal state %s, current %s', self.current_job._status, self.current_job.status)
        # status hasn't changed
        self.assertEqual(self.current_job.status, JobStatus.JOB_COMPLETED)
        logger.debug('%i => %s', len(self.current_job.job_history.values()), self.current_job.job_history.values())
        # assert that no history element has been added
        self.current_job.status = JobStatus.JOB_RUNNING
        self.current_job.run_cancel()
        self.assertTrue(self.current_job.status == JobStatus.JOB_CANCELLED)
        self.current_job.delete()
