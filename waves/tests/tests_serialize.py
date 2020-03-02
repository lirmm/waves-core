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
import json
import logging
from os.path import join

from django.test import override_settings
from django.conf import settings

from waves.core.import_export import ServiceSerializer
from waves.models import Service
from .base import WavesTestCaseMixin, bootstrap_services

logger = logging.getLogger(__name__)


@override_settings(
    WAVES_CORE={
        'DATA_ROOT': join(getattr(settings, 'BASE_DIR'), 'tests', 'data'),
        'JOB_BASE_DIR': join(settings.BASE_DIR, 'tests', 'data', 'jobs'),
        'ADMIN_EMAIL': 'admin@test-waves.com'
    }
)
class SerializationTestCase(WavesTestCaseMixin):

    def test_serialize_service(self):
        services = bootstrap_services()
        init_count = len(services)
        self.assertGreater(init_count, 0)
        file_paths = []
        for srv in Service.objects.all():
            file_out = srv.serialize()
            logger.debug("Serialized to %s", file_out)
            file_paths.append(file_out)
        for exp in file_paths:
            with open(exp) as fp:
                serializer = ServiceSerializer(data=json.load(fp))
                if serializer.is_valid():
                    serializer.save()
        self.assertEqual(init_count * 2, Service.objects.all().count())
