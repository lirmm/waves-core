from __future__ import unicode_literals

import importlib
import pkgutil
from inspect import getmembers, isabstract, isclass

from waves.adaptors.core.adaptor import JobAdaptor, AdaptorImporter
import waves.adaptors.addons

__all__ = ['load_addons']


def isAdaptorClass(value):
    return not isabstract(value) and isclass(value)


def load_core():
    return sorted(__load_adaptors('waves.adaptors.core', parent=JobAdaptor), key=lambda x: x[0])


def load_addons():
    return sorted(__load_adaptors('waves.adaptors.addons', parent=JobAdaptor), key=lambda x: x[0])


def load_importers():
    return sorted(__load_adaptors('waves.adaptors.importers', parent=AdaptorImporter), key=lambda x: x[0])


def __load_adaptors(path, parent):
    submodules = __import_submodules(path, True)
    adaptors = []
    for submodule_name, submodule in submodules.items():
        adaptors.extend([mem for mem in getmembers(submodule, isAdaptorClass)
                         if mem[1].__module__ == submodule.__name__ and issubclass(mem[1], parent)])
    return adaptors


def __import_submodules(package, recursive=True):
    """ Import all submodules of a module, recursively, including subpackages

    :param package: package (name or actual module)
    :type package: str | module
    :rtype: dict[str, types.ModuleType]
    """
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__path__ + '.' + name
        results[full_name] = importlib.import_module(full_name)
        if recursive and is_pkg:
            results.update(__import_submodules(full_name))
    return results
