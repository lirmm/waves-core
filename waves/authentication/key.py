""" Authentication base on a get parameter 'api_key'"""
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from rest_framework import authentication, exceptions

from waves.authentication.models import ApiKey


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

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        try:
            api_key = ApiKey.objects.select_related('user').get(key=key)
        except ApiKey.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid api key.'))

        if not api_key.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))
        return (api_key.user, api_key)
