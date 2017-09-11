from __future__ import unicode_literals

from django.utils.module_loading import import_string, import_module

__all__ = ['FastME']


def get_commands_impl_list():
    classes_list = [('', 'Select a implementation class...')]
    mod = import_module('waves.wcore.commands')
    for cls in sorted(mod.__all__):
        clazz = import_string(mod.__name__ + '.' + cls)
        classes_list.append((clazz.__module__ + '.' + clazz .__name__, clazz.__name__))
    return classes_list
