from __future__ import unicode_literals

import os
import unittest

from django.test import TestCase

import test_settings
import waves.wcore.adaptors.const
from waves.wcore.adaptors.cluster import LocalClusterAdaptor, SshClusterAdaptor
from waves.wcore.adaptors.exceptions import AdaptorException
from waves.wcore.adaptors.shell import LocalShellAdaptor, SshShellAdaptor, SshKeyShellAdaptor
from waves.wcore.tests.tests_utils import *
from waves.wcore.tests.base import WavesBaseTestCase
from waves.wcore.utils.encrypt import Encrypt

logger = logging.getLogger('tests')

NO_CLUSTER_MESSAGE = "A valid local SGE cluster is needed to run this tests"
MISSING_TOOL_MESSAGE = "Executable script is not in PATH : %s"


def skip_unless_sge():
    if not any(os.path.islink(os.path.join(_, 'qsub')) for _ in os.environ['PATH'].split(os.pathsep)):
        return unittest.skip(NO_CLUSTER_MESSAGE)
    return lambda f: f


class RunnerTestCase(WavesBaseTestCase, TestJobWorkflowMixin):
    tests_dir = dirname(__file__)
    loader = AdaptorLoader
    adaptors = [
        LocalShellAdaptor(command='cp'),
        LocalClusterAdaptor(protocol='sge', queue=test_settings.WAVES_LOCAL_TEST_SGE_CELL, command='cp'),
        SshShellAdaptor(protocol='ssh', command='cp', user_id=test_settings.WAVES_TEST_SSH_USER_ID,
                        password=Encrypt.encrypt(test_settings.WAVES_TEST_SSH_USER_PASS),
                        basedir=test_settings.WAVES_TEST_SSH_BASE_DIR,
                        host=test_settings.WAVES_TEST_SSH_HOST),
        SshClusterAdaptor(protocol='sge', command='cp',
                          queue=test_settings.WAVES_SSH_TEST_SGE_CELL,
                          user_id=test_settings.WAVES_TEST_SSH_USER_ID,
                          password=Encrypt.encrypt(test_settings.WAVES_TEST_SSH_USER_PASS),
                          basedir=test_settings.WAVES_SSH_TEST_SGE_BASE_DIR,
                          host=test_settings.WAVES_TEST_SSH_HOST),
        SshClusterAdaptor(protocol='slurm', command='cp', queue=test_settings.WAVES_SSH_TEST_SGE_CELL,
                          user_id=test_settings.WAVES_TEST_SSH_USER_ID,
                          password=Encrypt.encrypt(test_settings.WAVES_TEST_SSH_USER_PASS),
                          basedir=test_settings.WAVES_SSH_TEST_SGE_BASE_DIR,
                          host=test_settings.WAVES_TEST_SSH_HOST),
        SshKeyShellAdaptor(command='cp', user_id=test_settings.WAVES_SSH_KEY_USER_ID,
                           password=Encrypt.encrypt(test_settings.WAVES_SSH_KEY_PASSPHRASE),
                           basedir=test_settings.WAVES_SSH_KEY_BASE_DIR,
                           host=test_settings.WAVES_SSH_KEY_HOST)
    ]

    def testSerializeUnserialize(self):
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

    def testProtocol(self):
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

    def testCredentials(self):
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

    def testCpLocalJob(self):
        adaptor = self.adaptors[0]
        logger.debug('Connecting to %s', adaptor.name)
        sample_file = join(self.tests_dir, 'data', 'sample', 'test_copy.txt')
        job = create_cp_job(source_file=sample_file, submission=self._create_random_service().default_submission)
        job.adaptor = adaptor
        logger.info('job command line %s ', job.command_line)
        copied_file = join(job.working_dir, 'dest_copy.txt')
        source_file = join(job.working_dir, 'test_copy.txt')
        self.run_job_workflow(job)
        with open(source_file) as source, open(copied_file) as copy:
            self.assertEqual(source.read(), copy.read())
        self.assertTrue(job.results_available)
        self.assertEqual(job.status, waves.wcore.adaptors.const.JOB_TERMINATED)

    def testAllCpJob(self):
        for adaptor in self.adaptors:
            try:
                if adaptor.available:
                    logger.debug('Connecting to %s', adaptor.name)
                    sample_file = join(self.tests_dir, 'data', 'sample', 'test_copy.txt')
                    job = create_cp_job(source_file=sample_file, submission=self._create_random_service().default_submission)
                    adaptor.command = 'cp'
                    job.adaptor = adaptor
                    self.run_job_workflow(job)
                    self.assertTrue(job.results_available)
                    self.assertGreaterEqual(job.status, waves.wcore.adaptors.const.JOB_TERMINATED)
            except IOError as e:
                logger.info('Excepted file not present for job %s ', job)
                logger.exception(e.message)
            except AdaptorException as e:
                logger.info('Adaptor %s is not locally available',  adaptor)
                logger.exception(e.message)
