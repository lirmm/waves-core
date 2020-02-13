import logging

from django.utils.module_loading import import_string

from waves.adaptors.base import JobAdaptor
from waves.core.models import Runner
from waves.core.tests.base import WavesTestCaseMixin, TestJobWorkflowMixin

logger = logging.getLogger(__name__)


# TODO add override config with list of expected runners instead of bootstrap_runners calls
class RunnerTestCase(WavesTestCaseMixin, TestJobWorkflowMixin):

    def bootstrap_runners(self):
        """ Create base models from all Current implementation parameters """
        self.runner = []
        from waves.adaptors.loader import AdaptorLoader
        loader = AdaptorLoader
        for adaptor in loader.get_adaptors():
            runner = Runner.objects.create(name="%s Runner" % adaptor.name,
                                           clazz='.'.join([adaptor.__module__, adaptor.__class__.__name__]))
            self.runner.append(runner)

        return self.runner

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
