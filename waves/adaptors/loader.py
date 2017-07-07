from __future__ import unicode_literals

import json

from waves.settings import waves_settings, import_from_string

__all__ = ['AdaptorLoader']


class AdaptorLoader(object):
    adaptors_classes = waves_settings.ADAPTORS_CLASSES

    @classmethod
    def get_adaptors(cls):
        return sorted([adaptor_class() for adaptor_class in cls.adaptors_classes])

    @classmethod
    def load(cls, clazz, **params):
        if params is None:
            params = {}
        return next((x(**params) for x in cls.adaptors_classes if x == clazz), None)

    @classmethod
    def serialize(cls, adaptor):
        return adaptor.serialize()

    @classmethod
    def unserialize(cls, serialized):
        json_data = json.loads(serialized)
        clazz = import_from_string(json_data['clazz'], None)
        return cls.load(clazz, **json_data['params'])
