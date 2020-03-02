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
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from waves.authentication.models import WavesApiUser


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_api_key(sender, instance=None, created=False, **kwargs):
    if not kwargs.get('raw', False) and (created or WavesApiUser.objects.filter(user=instance).count() == 0):
        WavesApiUser.objects.create(user=instance)
