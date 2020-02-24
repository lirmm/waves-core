from django.test import TestCase
from django.utils.module_loading import import_string

from waves.core.adaptors.base import JobAdaptor
from waves.core.tests.base import *
from waves.core.tests.utils import bootstrap_runners, bootstrap_services

logger = logging.getLogger(__name__)


class WavesModelsTestCase(TestCase):
    fixtures = ("accounts.json",)
    services = []
    runners = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.services = bootstrap_services()
        cls.runners = bootstrap_runners()

    def test_create_runner(self):
        for runner in self.runners:
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

    def test_create_service(self):
        self.assertGreater(len(self.services), 0)
        for service in self.services:
            self.assertEqual(service.submissions.count(), 1)
            # Assert that service params has a length corresponding to 'allowed override' value
            self.assertListEqual(sorted(service.run_params.keys()), sorted(service.runner.run_params.keys()))
            self.assertIsNotNone(service.api_name)
            self.assertEqual(service.status, Service.SRV_DRAFT)
            logger.debug('Service %s', service.api_name)
