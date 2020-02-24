"""waves_core URL Configuration

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
    path('', TemplateView.as_view(template_name='base.html')),
    path('django-sb-admin/', include('django_sb_admin.urls')),
    path('admin/', admin.site.urls),
    path('vali/', include('vali.urls')),
    path('waves/', include('waves.core.urls', namespace='core')),
    path('api/', include('waves.api.urls', namespace='wapi')),
    path('api-scheme', include_docs_urls(title='Waves API Documentation', public=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
              + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
