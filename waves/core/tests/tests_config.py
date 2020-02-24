import logging
from os.path import join

from django.conf import settings
from django.test import TestCase, override_settings

from core.adaptors.loader import AdaptorLoader
from waves.core.tests.base import WavesTestCaseMixin

logger = logging.getLogger(__name__)


class WavesConfigTest(TestCase, WavesTestCaseMixin):

    @override_settings(
        WAVES_CORE={
            'JOB_BASE_DIR': join(settings.BASE_DIR, 'tests', 'data', 'jobs'),
            'ADMIN_EMAIL': 'admin@test-waves.com'
        }
    )
    def test_overridden_config(self):
        from waves.core.settings import waves_settings
        self.assertEqual(waves_settings.JOB_BASE_DIR, join(settings.BASE_DIR, 'tests', 'data', 'jobs'))
        self.assertEqual(waves_settings.ADMIN_EMAIL, 'admin@test-waves.com')

    def test_loader(self):
        from waves.core.settings import waves_settings
        list_adaptors = AdaptorLoader.get_adaptors()
        self.assertTrue(all([clazz.__class__ in waves_settings.ADAPTORS_CLASSES for clazz in list_adaptors]))
        [logger.debug(c) for c in list_adaptors]
