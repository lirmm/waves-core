"""
WAVES proprietary optional settings
These settings may be overridden in your Django main configuration file
"""
from __future__ import unicode_literals

from os.path import join, dirname
from django.conf import settings


def __init_setting(var, default=None, override=None):
    """
    Get setting var value from possible locations:
     - check in Django base settings.py
     - if default is set, set settings value
     - return setting value

    :param var: var name to check
    :param default: default value
    :param override: override another app settings value
    :return: the setting final value
    """
    settings_val = getattr(settings, var, None)
    if settings_val is None:
        setattr(settings, var, default)
        settings_val = default
    if override is not None:
        # override another app variable if not specified in settings
        if getattr(settings, override, None) is None:
            setattr(settings, override, settings_val)
    # in any case, register default value to settings
    return settings_val

WAVES_VERSION = '1.1'
WAVES_DATA_ROOT = __init_setting('WAVES_DATA_ROOT', default=join(settings.BASE_DIR, 'data'))
WAVES_JOB_DIR = __init_setting('WAVES_JOB_DIR', default=join(WAVES_DATA_ROOT, 'jobs'))
WAVES_SAMPLE_DIR = __init_setting('WAVES_SAMPLE_DIR', default=join(settings.MEDIA_ROOT, 'sample'))
WAVES_UPLOAD_MAX_SIZE = __init_setting('WAVES_UPLOAD_MAX_SIZE', default=20 * 1024 * 1024)
WAVES_TEMPLATE_PACK = __init_setting('WAVES_TEMPLATE_PACK', default='bootstrap3', override='CRISPY_TEMPLATE_PACK')
WAVES_HOST = __init_setting('WAVES_HOST', default='http://localhost')
