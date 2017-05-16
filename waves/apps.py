"""
WAVES app Django application descriptor

"""
from __future__ import unicode_literals

from os.path import dirname
from django.apps import AppConfig

# DO NOT REMOVE !
from waves.compat import constance

__version_detail__ = '0.1.0'
__version__ = '0.1.0'
__author__ = 'Marc Chakiachvili, MAB Team'
__licence__ = 'GPLv3'
__copyright__ = "Copyright(C) 2016-2017, LIRMM - UM - CNRS"


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
