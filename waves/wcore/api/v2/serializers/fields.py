from rest_framework import serializers


class CommaSeparatedListField(serializers.ListField, serializers.ReadOnlyField):
    def to_representation(self, value):
        if ',' in value:
            str_txt = value.split(',')
            return super(CommaSeparatedListField, self).to_representation(str_txt)
        return super(CommaSeparatedListField, self).to_representation([])


class ListElementField(serializers.DictField, serializers.ReadOnlyField):
    def to_representation(self, value):
        list_values = []
        list_labels = []
        for line in value.splitlines():
            line_element = line.split('|')
            list_values.append(line_element[1])
            list_labels.append(line_element[0])
        final_list = {
            "labels": list_labels,
            "values": list_values
        }
        return super(ListElementField, self).to_representation(final_list)


class InputFormatField(serializers.Field):
    def to_representation(self, instance):
        return ', '.join(instance.splitlines()) if instance is not None else ''

    def to_internal_value(self, data):
        return data.replace(', ', '\n') if data else ''
