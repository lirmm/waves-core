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
from celery import Celery
from django.conf import settings
import os

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "waves_core.settings")
django.setup()

app = Celery('waves.core', broker_pool_limit=1, broker=settings.URL_BROKER, result_backend=settings.URL_BROKER)
app.autodiscover_tasks()
