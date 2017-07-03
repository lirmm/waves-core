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
    from waves.settings import waves_settings
    if not waves_settings.SECRET_KEY:
        errors.append(
            Error(
                "You must define SECRET_KEY entry in WAVES_CORE settings",
                hint='WAVES_CORE = {'
                     '...'
                     '  SECRET_KEY: "YOUR SECRET KEY"'
                     '...'
                     '}',
                obj=waves_settings,
                id='waves.E001',
            )
        )
    elif len(waves_settings.SECRET_KEY) != 32:
        errors.append(
            Error(
                'Waves settings secret key must be 32 char long str',
                hint='WAVES_CORE = {'
                     '...'
                     '  SECRET_KEY: "YOUR SECRET KEY"'
                     '...'
                     '}',
                obj=waves_settings,
                id='waves.E002',
            )
        )
    return errors
