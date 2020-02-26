"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the GNU GPL v3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       https://www.gnu.org/licenses/gpl-3.0.en.html
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import logging
import os
import unittest
from os.path import join

import radical.saga as rs
from django.conf import settings
from django.db.models import ObjectDoesNotExist
from django.test import override_settings

from tests.mocks import MockJobRunnerAdaptor
from waves.core.adaptors.saga import SshClusterAdaptor, LocalShellAdaptor, SshShellAdaptor, SshKeyShellAdaptor
from waves.core.const import JobStatus
from waves.core.exceptions import AdaptorException
from waves.core.exceptions import JobInconsistentStateError
from waves.core.loader import AdaptorLoader
from waves.core.utils import Encrypt
from waves.models import Job
from waves.settings import waves_settings
from .base import sample_service, sample_job, WavesTestCaseMixin

logger = logging.getLogger(__name__)

NO_CLUSTER_MESSAGE = "A valid local SGE cluster is needed to run this tests"
MISSING_TOOL_MESSAGE = "Executable script is not in PATH : %s"


def skip_unless_sge():
    if not any(os.path.islink(os.path.join(_, 'qsub')) for _ in os.environ['PATH'].split(os.pathsep)):
        return unittest.skip(NO_CLUSTER_MESSAGE)
    return lambda f: f


def skip_unless_slurm():
    if not any(os.path.islink(os.path.join(_, 'sbatch')) for _ in os.environ['PATH'].split(os.pathsep)):
        return unittest.skip(NO_CLUSTER_MESSAGE)
    return lambda f: f


class AdaptorTestCase(WavesTestCaseMixin):
    loader = AdaptorLoader

    def setUp(self):
        super(AdaptorTestCase, self).setUp()
        self.local = LocalShellAdaptor(command='cp')
        self.sshShell = SshShellAdaptor(command='cp',
                                        user_id=settings.WAVES_TEST_SSH_USER_ID,
                                        password=settings.WAVES_TEST_SSH_USER_PASS,
                                        basedir=settings.WAVES_TEST_SSH_BASE_DIR,
                                        host=settings.WAVES_TEST_SSH_HOST,
                                        port=settings.WAVES_TEST_SSH_PORT)
        self.localSge = SshClusterAdaptor(protocol='sge', command='cp',
                                          queue=settings.WAVES_TEST_SGE_CELL,
                                          basedir=settings.WAVES_TEST_SGE_BASE_DIR,
                                          host="localhost")
        self.sshSge = SshClusterAdaptor(protocol='sge', command='cp',
                                        queue=settings.WAVES_SSH_TEST_SGE_CELL,
                                        user_id=settings.WAVES_TEST_SSH_USER_ID,
                                        password=Encrypt.encrypt(
                                            settings.WAVES_TEST_SSH_USER_PASS),
                                        basedir=settings.WAVES_SSH_TEST_SGE_BASE_DIR,
                                        host=settings.WAVES_TEST_SSH_HOST)
        self.sshShell = SshKeyShellAdaptor(command='cp', user_id=settings.WAVES_SSH_KEY_USER_ID,
                                           password=Encrypt.encrypt(settings.WAVES_SSH_KEY_PASSPHRASE),
                                           basedir=settings.WAVES_SSH_KEY_BASE_DIR,
                                           host=settings.WAVES_SSH_KEY_HOST)
        self.sshSlurm = SshClusterAdaptor(protocol='slurm', command='cp',
                                          queue=settings.WAVES_SLURM_TEST_SSH_QUEUE,
                                          user_id=settings.WAVES_SLURM_TEST_SSH_USER_ID,
                                          password=settings.WAVES_SLURM_TEST_SSH_USER_PASS,
                                          basedir=settings.WAVES_SLURM_TEST_SSH_BASE_DIR,
                                          host=settings.WAVES_SLURM_TEST_SSH_HOST)
        self.adaptors = [self.local, self.localSge, self.sshSge, self.sshShell, self.sshSlurm]

    def test_serialize(self):
        for code, adaptor in self.adaptors:
            logger.info("Testing serialization for %s ", adaptor.name)
            try:
                serialized = AdaptorLoader.serialize(adaptor)
                unserialized = AdaptorLoader.unserialize(serialized)
                self.assertEqual(adaptor.__class__, unserialized.__class__)
                self.assertEqual(adaptor.command, unserialized.command)
            except AdaptorException as e:
                logger.exception("AdaptorException in %s: %s", adaptor.__class__.__name__, e)

    @skip_unless_sge
    def test_sge_protocol(self):
        local = self.localSge
        ssh = self.sshSge
        for adaptor in (local, ssh):
            logger.info("Testing availability for %s ", adaptor.name)
            try:
                if adaptor.available:
                    logger.debug("Saga host %s, protocol %s", adaptor.saga_host, adaptor.host)
                    self.assertTrue(adaptor.saga_host.startswith(adaptor.protocol))
            except AdaptorException as e:
                logger.exception("AdaptorException in %s: %s", adaptor.__class__.__name__, e)
            else:
                logger.info("Adaptor not available for testing protocol %s " % adaptor.name)

    def test_init(self):
        for adaptor in waves_settings.ADAPTORS_CLASSES:
            new_instance = self.loader.load(adaptor,
                                            host="localTestHost",
                                            protocol="httpTest",
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
            except (rs.exceptions.SagaException, AdaptorException) as e:
                self.skipTest("Host not availabmle")
                logger.error('Saga Exception in %s: %s', adaptor.__class__.__name__, e)

    def test_job_states(self):
        """
        Test exceptions raise when state inconsistency is detected in jobs
        """
        job = sample_job(sample_service())
        adaptor = MockJobRunnerAdaptor(command='faked', protocol='mock')
        logger.debug('Internal state %s, current %s', job._status, job.status)
        job.status = JobStatus.JOB_RUNNING
        logger.debug('Internal state %s, current %s', job._status, job.status)
        with self.assertRaises(JobInconsistentStateError):
            adaptor.prepare_job(job)

        logger.debug('Internal state %s, current %s', job._status, job.status)
        logger.debug('Test Run')
        job.status = JobStatus.JOB_UNDEFINED
        with self.assertRaises(JobInconsistentStateError):
            adaptor.run_job(job)
        logger.debug('Internal state %s, current %s', job._status, job.status)
        logger.debug('Test Cancel')
        job.status = JobStatus.JOB_COMPLETED
        with self.assertRaises(JobInconsistentStateError):
            adaptor.cancel_job(job)
        logger.debug('Internal state %s, current %s', job._status, job.status)
        # status hasn't changed
        self.assertEqual(job.status, JobStatus.JOB_COMPLETED)
        logger.debug('%i => %s', len(job.job_history.values()), job.job_history.values())
        # assert that no history element has been added
        job.status = JobStatus.JOB_RUNNING
        adaptor.cancel_job(job)
        self.assertTrue(job.status == JobStatus.JOB_CANCELLED)
        slug = job.slug
        job.delete()
        with self.assertRaises(ObjectDoesNotExist):
            Job.objects.get(slug=slug)
