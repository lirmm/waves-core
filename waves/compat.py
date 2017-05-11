""" Compatibility file to enable dependents apps behaviour """
from __future__ import unicode_literals
from django.conf import settings


try:
    if 'jet' in settings.INSTALLED_APPS:
        from jet.admin import CompactInline
    else:
        from django.contrib.admin import StackedInline
        class CompactInline(StackedInline):
            """ Inherit base class """
            pass
except ImportError:
    raise

try:
    if 'ckeditor' in settings.INSTALLED_APPS:
        from ckeditor.fields import RichTextField
    else:
        from django.db import models

        class RichTextField(models.TextField):
            """ Override RichTextField """
            pass
except ImportError:
    raise
try:
    if 'bootstrap_themes' in settings.INSTALLED_APPS:
        from bootstrap_themes import list_themes
    else:
        available_themes = (
            ('default', 'Default'),
        )

        def list_themes():
            return available_themes
except ImportError:
    raise


