""" Authentication base on a get parameter 'api_key'"""
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from rest_framework import authentication, exceptions

User = get_user_model()


class WavesAPiKeyAuthentication(authentication.BaseAuthentication):

    """ WAVES API authentication backend, api_key added to URI """
    def authenticate(self, request):
        """ Authenticate from api GET or POST 'api_key' param"""
        api_key = request.POST.get('api_key', request.GET.get('api_key', None))
        if not api_key:
            return None
        try:
            user = User.objects.get(api_key=api_key)
            if user.is_active:
                user_logged_in.send(sender=user.__class__, request=request, user=user)
        except User.DoesNotExists:
            raise exceptions.AuthenticationFailed("No Such User")
        return user, None
