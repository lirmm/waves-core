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
from django.utils.translation import ugettext_lazy as _
from rest_framework import authentication, exceptions
from rest_framework.authentication import TokenAuthentication

from waves.authentication.models import WavesApiUser


class WavesAuth(object):

    @staticmethod
    def check_api_user(waves_user, request):
        if waves_user.ip_list:
            ip_list = waves_user.ip_list.split(',')
            if 'REMOTE_ADDR' not in request.META:
                msg = _('Origin IP not sent, but expected.')
                raise exceptions.AuthenticationFailed(msg)
            if request.META['REMOTE_ADDR'] not in ip_list:
                msg = _('Invalid IP in header.')
                raise exceptions.AuthenticationFailed(msg)


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """ WAVES API authentication backend, api_key added to URI """

    def authenticate(self, request):
        auth = request.POST.get('api_key', request.GET.get('api_key', None))

        if not auth:
            return None

        try:
            token = auth
        except UnicodeError:
            msg = _('Invalid api key. api key string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)

        auth_tuple = self.authenticate_credentials(token)
        if auth_tuple:
            WavesAuth.check_api_user(auth_tuple[1], request)
        return auth_tuple

    def authenticate_credentials(self, key):
        try:
            api_key = WavesApiUser.objects.select_related('user').get(key=key)
        except WavesApiUser.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid api key.'))

        if not api_key.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))
        return api_key.user, api_key


class TokenAuthentication(TokenAuthentication):
    """
    Override classic TokenAuthentication processes to use WAVES dedicated user class
    """
    model = WavesApiUser
    # keyword override : from default Token to Bearer (compliance issue to RFC 6750 & OpenAPI 3.0)
    # Authorization: Token <token>
    # Authorization: Bearer <token>
    keyword = "Bearer"

    def authenticate(self, request):
        auth_tuple = super(TokenAuthentication, self).authenticate(request)
        if auth_tuple:
            WavesAuth.check_api_user(auth_tuple[1], request)
        return auth_tuple
