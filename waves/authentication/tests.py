from __future__ import unicode_literals

from rest_framework.views import Response
from rest_framework import status

from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from waves.authentication.key import ApiKeyAuthentication
from waves.wcore.api.views.base import WavesAuthenticatedView
from django.conf.urls import include, url
from django.test import override_settings

User = get_user_model()


class ApiViewTest(WavesAuthenticatedView):
    authentication_classes = [ApiKeyAuthentication]

    def get(self, request):
        return Response({"message": "Hello, world!"})

    def post(self, request):
        return Response({"message": "Hello, world 2 !"})


urlpatterns = [
    url(
        r'^test-key-auth$',
        ApiViewTest.as_view()
    )
]


@override_settings(ROOT_URLCONF='waves.authentication.tests')
class TestApiAuth(APITestCase):

    def test_auth(self):
        user = User.objects.create(username='Test', is_active=True)
        response = self.client.get('/test-key-auth')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.get('/test-key-auth', data={'api_key': user.auth_api_key})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post('/test-key-auth', data={'api_key': user.auth_api_key})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get('/test-key-auth', data={'api_key': "thisiswrongapikey"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
