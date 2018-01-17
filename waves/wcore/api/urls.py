from __future__ import unicode_literals

from django.conf.urls import url, include

urlpatterns = [
    url(r'^', include('waves.wcore.api.v2.urls', namespace='v2')),
    # url(r'^v1/', include('waves.wcore.api.v1.urls', namespace='v1')),
]
