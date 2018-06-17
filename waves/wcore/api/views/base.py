from __future__ import unicode_literals

from django.conf import settings
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView, Response
from rest_framework import renderers, schemas
from rest_framework.decorators import api_view, renderer_classes


class WavesAuthenticatedView(APIView):
    """ Base WAVES API view, set up for all subclasses permissions / authentication """
    permission_classes = [IsAuthenticated, ]

    def get_permissions(self):
        if settings.DEBUG:
            self.permission_classes = [AllowAny, ]
        return super(WavesAuthenticatedView, self).get_permissions()

@api_view(['GET',])
@renderer_classes([renderers.CoreJSONRenderer])
def schema_view(request):
    generator = schemas.SchemaGenerator(title='CoreJson API')
    return Response(generator.get_schema())
