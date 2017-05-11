from __future__ import unicode_literals

from rest_framework import serializers

from waves.models import ServiceCategory, Service
from .services import ServiceSerializer


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    """
    Service category serializer/unserializer
    """
    class Meta:
        model = ServiceCategory
        fields = ('url', 'name', 'short_description', 'tools')
        lookup_field = 'api_name'
        extra_kwargs = {
            'url': {'view_name': 'waves_api_v1:waves-services-category-detail', 'lookup_field': 'api_name'}
        }
        depth = 1

    tools = serializers.SerializerMethodField('get_active_tools')

    def get_active_tools(self, category):
        """ List enabled tools for Category """
        tool_queryset = Service.objects.get_api_services().filter(category=category)
        serializer = ServiceSerializer(instance=tool_queryset, many=True, context=self.context,
                                       fields=('name', 'version', 'url'))
        return serializer.data
