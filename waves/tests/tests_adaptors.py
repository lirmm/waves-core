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

import radical.saga as rs
from django.db.models import ObjectDoesNotExist

from waves.tests.mocks import MockJobRunnerAdaptor
from waves.core.adaptors.saga import SshClusterAdaptor, LocalShellAdaptor, SshShellAdaptor
from waves.core.const import JobStatus
from waves.core.exceptions import AdaptorException
from waves.core.exceptions import JobInconsistentStateError
from waves.core.loader import AdaptorLoader
from waves.models import Job
from waves.settings import waves_settings
from .base import sample_service, sample_job, WavesTestCaseMixin

logger = logging.getLogger(__name__)

NO_CLUSTER_MESSAGE = "A valid local SGE cluster is needed to run this tests"
MISSING_TOOL_MESSAGE = "Executable script is not in PATH : %s"


def skip_unless_slurm(func):
    if not any(os.path.islink(os.path.join(_, 'sbatch')) for _ in os.environ['PATH'].split(os.pathsep)):
        return unittest.skip(NO_CLUSTER_MESSAGE)
    return lambda f: f


class AdaptorTestCase(WavesTestCaseMixin):
    loader = AdaptorLoader

    def setUp(self):
        super(AdaptorTestCase, self).setUp()
        self.local = LocalShellAdaptor(command='cp')
        self.sshShell = SshShellAdaptor(command='cp',
                                        user_id='testuser',
                                        password='testuser',
                                        host='localhost',
                                        port=10022)
        self.sshSge = SshClusterAdaptor(protocol='sge',
                                        command='cp',
                                        queue='all',
                                        user_id='testuser',
                                        password='testuser',
                                        host='localhost',
                                        port=10022
                                        )
        self.sshSlurm = SshClusterAdaptor(protocol='slurm',
                                          command='cp',
                                          queue='main',
                                          user_id='testuser',
                                          password='testuser',
                                          host='localhost',
                                          port=10022)
        # TODO use docker to add a sge through ssh
        self.adaptors = [self.local, self.sshShell, self.sshSge, self.sshSlurm]

    def test_serialize(self):
        for adaptor in self.adaptors:
            logger.info("Testing serialization for %s ", adaptor.name)
            try:
                serialized = AdaptorLoader.serialize(adaptor)
                un_serialized = AdaptorLoader.unserialize(serialized)
                self.assertEqual(adaptor.__class__, un_serialized.__class__)
                self.assertEqual(adaptor.command, un_serialized.command)
            except AdaptorException as e:
                logger.exception("AdaptorException in %s: %s", adaptor.__class__.__name__, e)

    def test_sge_ssh(self):
        """ Test SGE over ssh on local cluster - deployed through Docker (Simple Echo Job)"""
        local = self.sshSge
        logger.info("Testing availability for %s ", local.name)
        self.assertTrue(local.available)
        try:
            if local.available:
                logger.debug("Saga host %s, protocol %s", local.saga_host, local.host)
                self.assertTrue(local.saga_host.startswith(local.protocol))
        except AdaptorException as e:
            logger.exception("AdaptorException in %s: %s", local.__class__.__name__, e)
        else:
            logger.info("Adaptor not available for testing protocol %s " % local.name)

    def test_init_loader(self):
        for adaptor in waves_settings.ADAPTORS_CLASSES:
            new_instance = self.loader.load(adaptor,
                                            host="localTestHost",
                                            protocol="httpTest",
                                            command="CommandTest")
            self.assertEqual(new_instance.host, "localTestHost")
            self.assertEqual(new_instance.command, "CommandTest")
            self.assertEqual(new_instance.protocol, "httpTest")

        list_adaptors = AdaptorLoader.get_adaptors()
        self.assertTrue(all([clazz.__class__ in waves_settings.ADAPTORS_CLASSES for clazz in list_adaptors]))
        [logger.debug(c) for c in list_adaptors]

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
                else:
                    logger.info('Adaptor not available %s: %s', adaptor.__class__.__name__)
            except (rs.exceptions.SagaException, AdaptorException) as e:
                logger.info('Adaptor not available %s: %s', adaptor.__class__.__name__, self.adaptor.connexion_string())

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
