"""waves_core URL Configuration

"""
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView

# import debug_toolbar
from rest_framework.documentation import include_docs_urls

admin.site.site_title = 'WAVES Administration'

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='base.html')),
    url(r'^admin/', admin.site.urls),
    url(r'^waves/admin/', include('waves.wcore.urls', namespace='wcore')),
    url(r'^waves/api/', include('waves.wcore.api.urls', namespace='wapi')),
    url(r'^api/docs/', include_docs_urls(title='Waves API Documentation', public=True)),
    url(r'^waves/', include('waves.front.urls', namespace='wfront')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
              + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
