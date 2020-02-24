"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the GNU GPL v3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       https://www.gnu.org/licenses/gpl-3.0.en.html
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
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
