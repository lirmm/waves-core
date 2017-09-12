"""waves_core URL Configuration

"""
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView

admin.site.site_title = 'WAVES Administration'

urlpatterns = [
        url(r'^$', TemplateView.as_view(template_name='base.html')),
        url(r'^admin/', admin.site.urls),
        url(r'^wcore/', include('waves.wcore.urls', namespace='wcore')),
        url(r'^waves/', include('waves.front.urls', namespace='wfront')),
        url(r'^waves/api/', include('waves.wcore.api.urls', namespace='wapi'))
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
      + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
