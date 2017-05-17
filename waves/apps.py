"""
WAVES app Django application descriptor

"""
from __future__ import unicode_literals

from os.path import dirname
from django.apps import AppConfig

# DO NOT REMOVE !
from waves.compat import constance


class WavesConfig(AppConfig):
    """
    WAVES main application AppConfig, add signals for waves_webapp
    """
    name = "waves"
    verbose_name = 'WAVES'
    path = dirname(__file__)

    def ready(self):
        """
        Executed once when WAVES application startup !
        Just import waves signals
        :return: None
        """
        import waves.signals
