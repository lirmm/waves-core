from __future__ import unicode_literals

from rest_framework import serializers
from waves.wcore.models.inputs import AParam


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    Optionally `hidden` parameter allows to hide some of the fields defined in Serializer

    """
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', [])
        hidden = kwargs.pop('hidden', [])
        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)
        if fields:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        elif hidden:
            initial = set(hidden)
            for field_name in initial:
                self.fields.pop(field_name)


class RecursiveField(serializers.ModelSerializer):
    class Meta:
        model = AParam

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        print self.parent.parent
        print value
        print self.parent
        return serializer.data
