from rest_framework import serializers


class CommaSeparatedListField(serializers.ListField, serializers.ReadOnlyField):
    def to_representation(self, value):
        if ',' in value:
            str_txt = value.split(',')
            return super(CommaSeparatedListField, self).to_representation(str_txt)
        return super(CommaSeparatedListField, self).to_representation([])


class ListElementField(serializers.ListField, serializers.ReadOnlyField):
    def to_representation(self, value):
        list_elements = []
        for line in value.splitlines():
            line_element = line.split('|')
            list_elements.append(line_element)
        return ', '.join(value.splitlines())


class InputFormatField(serializers.Field):
    def to_representation(self, instance):
        return ', '.join(instance.splitlines()) if instance is not None else ''

    def to_internal_value(self, data):
        return data.replace(', ', '\n') if data else ''