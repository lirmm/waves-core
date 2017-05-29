from __future__ import unicode_literals

from waves.settings import waves_settings, import_from_string

__all__ = ['AdaptorLoader']


class AdaptorLoader(object):
    adaptors_classes = waves_settings.ADAPTORS_CLASSES

    def get_adaptors(self):
        return sorted([adaptor_class() for adaptor_class in self.adaptors_classes])

    def get_adaptor(self, clazz, params):
        if clazz not in self.adaptors_classes:
            raise RuntimeError('This clazz is not defined as concrete adaptor')
        return self.adaptors_classes[clazz](**params)
