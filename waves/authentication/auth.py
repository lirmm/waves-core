""" Authentication base on a get parameter 'api_key'"""
from __future__ import unicode_literals

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

    def authenticate(self, request):
        auth_tuple = super(TokenAuthentication, self).authenticate(request)
        if auth_tuple:
            WavesAuth.check_api_user(auth_tuple[1], request)
        return auth_tuple
