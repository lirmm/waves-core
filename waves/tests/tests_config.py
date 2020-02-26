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
from os.path import join

from django.conf import settings
from django.test import TestCase, override_settings

from waves.core.loader import AdaptorLoader
from waves.tests.base import WavesTestCaseMixin

logger = logging.getLogger(__name__)


class WavesConfigTest(TestCase, WavesTestCaseMixin):

    @override_settings(
        WAVES_CORE={
            'JOB_BASE_DIR': join(settings.BASE_DIR, 'tests', 'data', 'jobs'),
            'ADMIN_EMAIL': 'admin@test-waves.com'
        }
    )
    def test_overridden_config(self):
        from waves.settings import waves_settings
        self.assertEqual(waves_settings.JOB_BASE_DIR, join(settings.BASE_DIR, 'tests', 'data', 'jobs'))
        self.assertEqual(waves_settings.ADMIN_EMAIL, 'admin@test-waves.com')

    def test_loader(self):
        from waves.settings import waves_settings
        list_adaptors = AdaptorLoader.get_adaptors()
        self.assertTrue(all([clazz.__class__ in waves_settings.ADAPTORS_CLASSES for clazz in list_adaptors]))
        [logger.debug(c) for c in list_adaptors]
