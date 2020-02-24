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
from waves.core.import_export import *
from waves.core.import_export.runners import *
from waves.core.import_export import *
from rest_framework.exceptions import ValidationError

from waves.core.import_export import *
from waves.core.import_export.runners import *
from waves.core.import_export import *


def check_db_version(func):
    def wrapper(*args, **kwargs):
        a = list(args)
        a.reverse()
        return func(*args, **kwargs)

    return func


class BaseSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('db_version',)

    db_version = serializers.CharField(max_length=10)


class RelatedSerializerMixin(object):
    """ Add serializers capability to create related easily"""

    # noinspection PyUnresolvedReferences
    def create_related(self, foreign, serializer, datas):
        """ Create related objects (foreign key to current service model object"""
        created = []
        for data in datas:
            try:
                ser = serializer(data=data)
                ser.is_valid(True)
                params = {key: value for key, value in foreign.items()}
                created.append(ser.save(**params))
            except ValidationError as e:
                self.errors[''] = e.detail
        return created
