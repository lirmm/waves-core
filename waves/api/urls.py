from django.conf.urls import url, include

# TODO restore schema_view
# from core import schema_view

app_name = "waves.api"

urlpatterns = [
    # Schema to be used with coreapi
    # url(r'^schema$', schema_view),
    url(r'^', include('waves.api.v2.urls', namespace='v2')),
    url(r'^v1/', include('waves.api.v1.urls', namespace='v1')),
]