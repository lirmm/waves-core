from __future__ import unicode_literals

from django.conf.urls import url, include
from django.conf import settings

urlpatterns = [
    url(r'^', include('waves.wcore.api.v2.urls', namespace='v2')),
    url(r'^v1/', include('waves.wcore.api.v1.urls', namespace='v1')),
]
if 'waves.authentication' in settings.INSTALLED_APPS:
    from waves.authentication import views
    urlpatterns.append(url(r'^api-token-auth', views.obtain_auth_token))
