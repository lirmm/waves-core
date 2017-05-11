"""WAVES models export module for Categories """
from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from waves.models import ServiceCategory


class CategorySerializer(serializers.ModelSerializer):
    """ Service Category serializer """
    class Meta:
        model = ServiceCategory
        fields = ('name', 'description', 'short_description', 'api_name', 'ref')
        validators = []

    name = serializers.CharField(validators=[])
    api_name = serializers.CharField(validators=[])

    def create(self, validated_data):
        """ Get or create a new instance, based on api_name """
        category, created = ServiceCategory.objects.get_or_create(api_name=validated_data.pop('api_name'),
                                                                  **validated_data)
        return category
