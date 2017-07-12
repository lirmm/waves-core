from rest_framework.exceptions import ValidationError


class RelatedSerializerMixin(object):
    """ Add serializers capability to create related easily"""

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
