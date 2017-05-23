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
        fields = ('url', 'name', 'parent', 'short_description', 'tools', 'sub_categories')
        lookup_field = 'api_name'
        extra_kwargs = {
            'url': {'view_name': 'waves:api_v2:waves-services-category-detail', 'lookup_field': 'api_name'},
        }
        depth = 1

    sub_categories = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        source='children_category',
        view_name='waves:api_v2:waves-services-category-detail',
        lookup_field='api_name'
    )
    parent = serializers.HyperlinkedRelatedField(
        many=False,
        read_only=True,
        view_name='waves:api_v2:waves-services-category-detail',
        lookup_field='api_name'
    )

    tools = serializers.SerializerMethodField()

    def get_tools(self, category):
        """ List enabled tools for Category """
        tool_queryset = Service.objects.filter(category=category)
        serializer = ServiceSerializer(instance=tool_queryset, many=True, context=self.context,
                                       fields=('name', 'version', 'url'))
        return serializer.data
