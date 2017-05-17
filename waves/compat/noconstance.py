"""
Compatibility in case constance is not in installed apps
"""
from __future__ import unicode_literals

from waves.settings import waves_settings


class config(object):
    """ Fake constance config class to enable compatibility in waves files (accessing directly constance config var 
    from config object """
    def __getattr__(self, item):
        return getattr(waves_settings, item)
    pass
