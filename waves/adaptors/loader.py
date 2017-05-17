from __future__ import unicode_literals

import importlib
import pkgutil
from inspect import getmembers, isabstract, isclass

import waves.settings
import waves.adaptors.addons
from importlib import import_module

__all__ = ['AdaptorLoader']


def import_from_string(val):
    """
    Attempt to import a class from a string representation.
    """
    try:
        # Nod to tastypie's use of importlib.
        parts = val.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        msg = "Could not import '%s' for WAVES settings '%s': %s." % (val, e.__class__.__name__, e)
        raise ImportError(msg)


class AdaptorLoader(object):
    adaptors_classes = waves.settings.WAVES_ADAPTORS_CLASSES

    def get_adaptors(self):
        return sorted([adaptor_class() for adaptor_class in [import_from_string(item) for item in self.adaptors_classes]])
