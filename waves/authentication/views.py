from __future__ import unicode_literals

from rest_framework import parsers, renderers
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WavesApiUser
from .serializers import WavesApiUserSerializer


class ObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = WavesApiUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = WavesApiUser.objects.get_or_create(user=user)
        return Response({'auth_api_key': token.key})

obtain_auth_token = ObtainAuthToken.as_view()
