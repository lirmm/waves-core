from __future__ import unicode_literals, print_function

import logging

from django.utils.module_loading import import_string

from waves.wcore.adaptors import JobAdaptor
from waves.wcore.tests.base import BaseTestCase, TestJobWorkflowMixin

logger = logging.getLogger(__name__)


class RunnerTestCase(BaseTestCase, TestJobWorkflowMixin):
    def test_create_runner(self):
        for runner in self.bootstrap_runners():
            logger.info('Current: %s - %s', runner.name, runner.clazz)
            adaptor = runner.adaptor
            self.assertIsInstance(adaptor, JobAdaptor)
            self.assertEqual(runner.run_params.__len__(), adaptor.init_params.__len__())
            self.assertListEqual(sorted(runner.run_params.keys()), sorted(adaptor.init_params.keys()))
            obj_runner = import_string(runner.clazz)
            expected_params = obj_runner().init_params
            runner_params = runner.run_params
            logger.debug("Expected %s", expected_params)
            logger.debug("Defaults %s", runner_params)
            logger.debug("Config %s", runner.adaptor._dump_config())
            self.assertEquals(sorted(expected_params), sorted(runner_params))
