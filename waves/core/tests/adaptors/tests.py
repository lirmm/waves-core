import logging

from django.test import TestCase
from django.utils.module_loading import import_string

from waves.core.tests.base import bootstrap_adaptors
from waves.core.adaptors.base import JobAdaptor

logger = logging.getLogger(__name__)


class RunnerTestCase(TestCase):

    def test_create_runner(self):
        for runner in bootstrap_adaptors():
            logger.info('Current: %s - %s', runner.name, runner.clazz)
            adaptor = runner.adaptor
            self.assertIsInstance(adaptor, JobAdaptor)
            self.assertListEqual(sorted(runner.run_params.keys()), sorted(adaptor.init_params.keys()))
            obj_runner = import_string(runner.clazz)
            expected_params = obj_runner().init_params
            runner_params = adaptor.init_params
            logger.debug("Expected %s", expected_params)
            logger.debug("Defaults %s", runner_params)
            logger.debug("Config %s", adaptor.dump_config())
            self.assertEquals(sorted(expected_params), sorted(runner_params))
