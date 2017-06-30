from __future__ import unicode_literals

import os
import unittest

from django.conf import settings
from django.test import TestCase

import test_settings
import waves.adaptors.const
from waves.adaptors.core.cluster import LocalClusterAdaptor, SshClusterAdaptor
from waves.adaptors.core.shell import LocalShellAdaptor, SshShellAdaptor, SshKeyShellAdaptor
from waves.adaptors.exceptions import AdaptorException, AdaptorConnectException
from waves.tests.utils import *
from waves.utils.encrypt import Encrypt

logger = logging.getLogger('tests')

NO_CLUSTER_MESSAGE = "A valid local SGE cluster is needed to run this tests"
MISSING_TOOL_MESSAGE = "Executable script is not in PATH : %s"


def skip_unless_sge():
    if not any(os.path.islink(os.path.join(_, 'qsub')) for _ in os.environ['PATH'].split(os.pathsep)):
        return unittest.skip(NO_CLUSTER_MESSAGE)
    return lambda f: f


class RunnerTestCase(TestCase):
    tests_dir = dirname(__file__)
    loader = AdaptorLoader()

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

    def testProtocol(self):
        for adaptor in self.adaptors:
            logger.info("Testing availability for %s ", adaptor.name)
            if adaptor.available:
                logger.debug("Saga host %s, protocol %s", adaptor.saga_host, adaptor.host)
                self.assertTrue(adaptor.saga_host.startswith(adaptor.protocol))
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

            if adaptor.available:
                try:
                    self.adaptor = adaptor
                    self.adaptor.connect()
                    self.assertTrue(self.adaptor.connected)
                    logger.debug('Connected to %s ', self.adaptor.connexion_string())
                    self.adaptor.disconnect()
                except AdaptorConnectException as e:
                    self.fail('Connexion error: %s ' % e.message)
                except AdaptorException as e:
                    logger.exception(e.get_full_message())
            else:
                logger.info('Adaptor %s is not locally available' % adaptor)

    def testCpLocalJob(self):
        adaptor = self.adaptors[0]
        logger.debug('Connecting to %s', adaptor.name)
        sample_file = join(self.tests_dir, 'data', 'sample', 'test_copy.txt')
        job = create_cp_job(source_file=sample_file)
        job.adaptor = adaptor
        logger.info('job command line %s ', job.command_line)
        copied_file = join(job.working_dir, 'dest_copy.txt')
        source_file = join(job.working_dir, 'test_copy.txt')
        run_job_workflow(job)
        with open(source_file) as source, open(copied_file) as copy:
            self.assertEqual(source.read(), copy.read())
        self.assertTrue(job.results_available)
        self.assertEqual(job.status, waves.adaptors.const.JOB_TERMINATED)

    def testAllCpJob(self):
        for adaptor in self.adaptors:
            if adaptor.available:
                try:
                    logger.debug('Connecting to %s', adaptor.name)
                    sample_file = join(self.tests_dir, 'data', 'sample', 'test_copy.txt')
                    job = create_cp_job(source_file=sample_file)
                    adaptor.command = 'cp'
                    job.adaptor = adaptor
                    run_job_workflow(job)
                    copied_file = join(job.working_dir, 'dest_copy.txt')
                    source_file = join(job.working_dir, 'test_copy.txt')
                    with open(source_file) as source, open(copied_file) as copy:
                        self.assertEqual(source.read(), copy.read())
                    self.assertTrue(job.results_available)
                    self.assertEqual(job.status, waves.adaptors.const.JOB_TERMINATED)
                except AdaptorException as e:
                    logger.exception(e.get_full_message())
            else:
                logger.info('Adaptor %s is not locally available' % adaptor)
