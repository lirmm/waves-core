""" WAVES API categories endpoints """
from __future__ import unicode_literals

from rest_framework import viewsets

from waves.models import ServiceCategory
from ..serializers import CategorySerializer

__all__ = ['CategoryViewSet']


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API entry point to list services categories
    """
    queryset = ServiceCategory.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'api_name'
