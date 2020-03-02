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
from django.conf.urls import url
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APITestCase
from rest_framework.views import Response

from waves.api.views.base import WavesAuthenticatedView

User = get_user_model()


class ApiViewTest(WavesAuthenticatedView):
    # authentication_classes = [ApiKeyAuthentication]
    permission_classes = [IsAuthenticated]

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

    def test_api_key_auth(self):
        user = User.objects.create(username='Test', is_active=True)
        response = self.client.get('/test-key-auth')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.get('/test-key-auth', data={'api_key': user.waves_user.key})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post('/test-key-auth', data={'api_key': user.waves_user.key})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get('/test-key-auth', data={'api_key': "thisiswrongapikey"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_auth(self):
        user = User.objects.create(username='TestAnother', is_active=True)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.waves_user.key)
        response = self.client.get('/test-key-auth')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_domain(self):
        user = User.objects.create(username='TestDomain', is_active=True)
        # No domain / ip list at all
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.waves_user.key)
        response = self.client.get('/test-key-auth')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.waves_user.domain = 'waves.test.com'
        user.waves_user.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.waves_user.key)

        user.waves_user.ip_list = '127.0.0.1,127.1.1.0'
        user.waves_user.domain = None
        user.waves_user.save()
        response = self.client.get('/test-key-auth', **{'REMOTE_ADDR': "193.168.1.25"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.get('/test-key-auth', **{'REMOTE_ADDR': "127.0.0.1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
