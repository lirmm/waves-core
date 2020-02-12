"""
WAVES app Django application descriptor

"""

from django.apps import AppConfig


# noinspection PyUnresolvedReferences
class WavesApiConfig(AppConfig):
    """
    WAVES main application AppConfig, add signals for waves_webapp
    """
    name = "waves.api"
    verbose_name = 'WAVES API CORE'


