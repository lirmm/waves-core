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
from django.contrib import admin

from waves.authentication.models import WavesApiUser


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created')
    fields = ('user', 'created', 'key', 'ip_list', 'domain')
    ordering = ('-created',)
    readonly_fields = ('user', 'created', 'key')


admin.site.register(WavesApiUser, ApiKeyAdmin)
