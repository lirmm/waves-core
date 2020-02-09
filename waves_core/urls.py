"""waves_core URL Configuration

"""


from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from rest_framework.documentation import include_docs_urls

admin.site.site_title = 'WAVES Administration'

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='base.html')),
    url(r'^admin/', admin.site.urls),
    url(r'^waves/', include('waves.urls', namespace='core')),
    url(r'^api/', include('waves.api.urls', namespace='wapi')),
    # Browsable API documentation
    url(r'^api-scheme', include_docs_urls(title='Waves API Documentation', public=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
