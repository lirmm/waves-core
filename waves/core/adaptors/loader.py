import json

from waves.core.adaptors.exceptions import AdaptorNotAvailableException
from waves.settings import import_from_string

__all__ = ['AdaptorLoader']


class AdaptorLoader(object):

    @classmethod
    def get_adaptors(cls):
        from waves.settings import waves_settings
        return sorted([adaptor_class() for adaptor_class in waves_settings.ADAPTORS_CLASSES],
                      key=lambda clazz: clazz.__class__.__name__)

    @classmethod
    def load(cls, clazz, **params):
        from waves.settings import waves_settings

        if params is None:
            params = {}
        loaded = next((x(**params) for x in waves_settings.ADAPTORS_CLASSES if x == clazz), None)
        if loaded is None:
            raise AdaptorNotAvailableException("This adapter class %s is not available " % clazz)
        return loaded

    @classmethod
    def serialize(cls, adaptor):
        return adaptor.serialize()

    @classmethod
    def unserialize(cls, serialized):
        json_data = json.loads(serialized)
        clazz = import_from_string(json_data['clazz'])
        return cls.load(clazz, **json_data['params'])

    @classmethod
    def get_class_names(cls):
        from waves.settings import waves_settings
        return ['{}.{}'.format(clazz.__module__, clazz.__name__) for clazz in waves_settings.ADAPTORS_CLASSES]
