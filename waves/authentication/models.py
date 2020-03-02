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
import binascii
import os

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from waves.settings import waves_settings


class WavesApiUser(models.Model):
    """
    The default authorization token model.
    """
    key = models.CharField(_("Key"), max_length=40, primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name='waves_user',
        on_delete=models.CASCADE, verbose_name=_("User")
    )
    created = models.DateTimeField(_("Created"), auto_now_add=True)
    domain = models.CharField(_('Origin URL(s)'), null=True, blank=True, max_length=255,
                              help_text="Comma separated list")
    ip_list = models.CharField(_('Ip(s) List'), null=True, blank=True, max_length=255, help_text="Comma separated list")

    class Meta:
        abstract = 'waves.authentication' not in settings.INSTALLED_APPS
        verbose_name = _("Waves Api auth")
        verbose_name_plural = _("Waves Api auths")

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(WavesApiUser, self).save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key

    @property
    def main_domain(self):
        return self.domain.split(",")[0] if self.domain else waves_settings.HOST
