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
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from rest_framework.documentation import include_docs_urls

admin.site.site_title = 'WAVES'

urlpatterns = [
    path('', TemplateView.as_view(template_name='waves/base.html')),
    path('django-sb-admin/', include('django_sb_admin.urls')),
    path('admin/', admin.site.urls),
    path('vali/', include('vali.urls')),
    path('waves/', include('waves.urls', namespace='core')),
    path('api/', include('waves.api.urls', namespace='wapi')),
    path('api-scheme', include_docs_urls(title='Waves API Documentation', public=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
              + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
