from __future__ import unicode_literals

import json

from waves.wcore.settings import waves_settings, import_from_string
from waves.wcore.adaptors.exceptions import AdaptorNotAvailableException

__all__ = ['AdaptorLoader']


class AdaptorLoader(object):
    adaptors_classes = waves_settings.ADAPTORS_CLASSES

    @classmethod
    def get_adaptors(cls):
        return sorted([adaptor_class() for adaptor_class in cls.adaptors_classes])

    def init_value_editable(self, init_param):
        if init_param == 'protocol':
            return False
        return super(LocalShellAdaptor, self).init_value_editable(init_param)


    @classmethod
    def load(cls, clazz, **params):
        if params is None:
            params = {}
        loaded = next((x(**params) for x in cls.adaptors_classes if x == clazz), None)
        if loaded is None:
            raise AdaptorNotAvailableException("This adaptor class %s is not available " % clazz)
        return loaded

    @classmethod
    def serialize(cls, adaptor):
        return adaptor.serialize()

    @classmethod
    def unserialize(cls, serialized):
        json_data = json.loads(serialized)
        clazz = import_from_string(json_data['clazz'])
        return cls.load(clazz, **json_data['params'])
