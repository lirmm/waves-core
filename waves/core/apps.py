"""
WAVES app Django application descriptor

"""
from __future__ import unicode_literals

from os.path import dirname
from django.apps import AppConfig
from django.core.checks import Error, Warning, register


class WavesConfig(AppConfig):
    """
    WAVES main application AppConfig, add signals for waves_webapp
    """
    name = "waves.core"
    verbose_name = 'WAVES CORE '
    path = dirname(__file__)

    def ready(self):
        """
        Executed once when WAVES application startup !
        Just import waves signals
        :return: None
        """
        import waves.core.signals


@register()
def check_waves_config(app_configs=('waves'), **kwargs):
    """
    WAVES configuration check up, added to classic ``manage.py check`` Django command

    .. TODO:
        Add more control on WAVES configuration

    :param app_configs:
    :param kwargs:
    :return:
    """
    errors = []
    # check values for SECRET_KEY
    from waves.core.settings import waves_settings
    if len(waves_settings.SECRET_KEY) != 32:
        errors.append(
            Error(
                'Waves need Django SECRET_KEY being at least 32 characters long',
                hint='WAVES_CORE = {'
                     '...'
                     '  SECRET_KEY: "YOUR SECRET KEY"'
                     '...'
                     '}',
                obj=waves_settings,
                id='waves.core.E002',
            )
        )
    elif len(waves_settings.ADAPTORS_CLASSES) == 0:
        errors.append(
            Error(
                'You set ADAPTORS_CLASSES but empty, WAVES needs ADAPTORS tu run JOB',
                hint='Either remove your empty entry or setup your classes',
                obj=waves_settings,
                id='waves.core.E003',
            )
        )
    return errors
