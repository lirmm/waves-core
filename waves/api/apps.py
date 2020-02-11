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

    def ready(self):
        """
        Executed once when WAVES application startup !
        Just import waves signals
        :return: None
        """
        from waves.api.v2 import serializers
        from waves.api.v2 import views
