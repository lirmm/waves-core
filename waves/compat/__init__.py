""" 
Compatibility file to enable dependents apps behaviour 
"""
from __future__ import unicode_literals

from django.conf import settings
from django.contrib.admin import StackedInline

__all__ = ["available_themes", "list_themes", "RichTextField", "CompactInline", 'organize_input_class',
           "SortableInlineAdminMixin"]


if 'jet' in settings.INSTALLED_APPS:
    from compat_jet import *
    organize_input_class = 'waves.compat.submissions_jet.OrganizeInputInline'
else:
    organize_input_class = 'waves.compat.submissions_std.OrganizeInputInline'

    class CompactInline(StackedInline):
        """ Inherit base class """
        pass

if 'ckeditor' in settings.INSTALLED_APPS:
    from compat_ckeditor import *
else:
    from django.db import models

    class RichTextField(models.TextField):
        """ Override RichTextField """
        pass

if 'bootstrap_themes' in settings.INSTALLED_APPS:
    from compat_bootstrap_themes import *
else:
    available_themes = (
        ('default', 'Default'),
    )

    def list_themes():
        return available_themes

if 'adminsortable2' not in settings.INSTALLED_APPS:
    class SortableInlineAdminMixin(object):
        pass
else:
    from compat_adminsortable import *
