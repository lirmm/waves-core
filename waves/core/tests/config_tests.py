import logging
from os.path import join

from django.conf import settings
from django.test import TestCase, override_settings

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
