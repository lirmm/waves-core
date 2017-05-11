from __future__ import unicode_literals

from django.conf import settings
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView


class WavesBaseView(APIView):
    """ Base WAVES API view, set up for all subclasses permissions / authentication """
    permission_classes = [IsAuthenticated, ]

    def get_permissions(self):
        if settings.DEBUG:
            self.permission_classes = [AllowAny,]
        return super(WavesBaseView, self).get_permissions()
