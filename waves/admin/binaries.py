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
from os.path import isfile

from django.contrib import admin

from .base import WavesModelAdmin
from waves.models import ServiceBinaryFile


@admin.register(ServiceBinaryFile)
class ServiceBinaryFileAdmin(WavesModelAdmin):
    model = ServiceBinaryFile
    list_display = ('label', 'created', 'updated', 'file_size', 'file_path')

    def file_size(self, obj):
        if isfile(obj.binary.path):
            return '%s ko' % (obj.binary.size / 1024)
        return "N/A"

    def file_path(self, obj):
        if isfile(obj.binary.path):
            return obj.binary.path
        return "N/A"

    def get_model_perms(self, request):
        # Disable direct entry to BinaryFiles
        return {}
