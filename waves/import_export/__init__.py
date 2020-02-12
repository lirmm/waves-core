from rest_framework.exceptions import ValidationError
from import_export.services import *
from import_export.runners import *
from import_export.jobs import *
from rest_framework.exceptions import ValidationError



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
