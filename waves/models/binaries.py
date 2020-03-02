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

from django.db import models

from waves.core.utils.storage import binary_storage, binary_directory
from .base import Slugged, TimeStamped

__all__ = ['ServiceBinaryFile']


class ServiceBinaryFile(Slugged, TimeStamped):
    class Meta:
        verbose_name = 'Binary file'
        verbose_name_plural = 'Binaries files'
        db_table = 'wcore_servicebinaryfile'
        app_label = "waves"

    label = models.CharField('Binary file label', max_length=255, null=False)
    binary = models.FileField('Binary file', upload_to=binary_directory, storage=binary_storage)

    def __str__(self):
        return self.label

    def __unicode__(self):
        return self.label
