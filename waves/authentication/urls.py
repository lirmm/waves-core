from django.conf.urls import url

from core import views

urlpatterns = [
    url(r'^api-token-auth', views.obtain_auth_token)
]
