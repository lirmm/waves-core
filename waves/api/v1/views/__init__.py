""" WAVES API views """
from __future__ import unicode_literals

from rest_framework import permissions
from rest_framework.views import APIView


class WavesBaseView(APIView):
    """ Base WAVES API view, set up for all subclasses permissions / authentication """
    permission_classes = (permissions.IsAuthenticated, )

    def get_permissions(self):
        return super(WavesBaseView, self).get_permissions()
