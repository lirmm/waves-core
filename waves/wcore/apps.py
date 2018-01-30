"""
WAVES app Django application descriptor

"""
from __future__ import unicode_literals

from django.apps import AppConfig
from django.core.checks import Error, register
from django.conf import settings


class WavesConfig(AppConfig):
    """
    WAVES main application AppConfig, add signals for waves_webapp
    """
    name = "waves.wcore"
    verbose_name = 'WAVES CORE '

    def ready(self):
        """
        Executed once when WAVES application startup !
        Just import waves signals
        :return: None
        """
        from waves.wcore import signals


@register()
def check_waves_config(app_configs=('waves.wcore',), **kwargs):
    """
    WAVES configuration check up, added to classic ``manage.py check`` Django command

    :param app_configs:
    :param kwargs:
    :return:
    """
    errors = []
    # check values for SECRET_KEY
    from waves.wcore.settings import waves_settings
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
                id='waves.wcore.E001',
            )
        )
    elif len(waves_settings.ADAPTORS_CLASSES) == 0:
        errors.append(
            Error(
                'You set ADAPTORS_CLASSES but empty, WAVES needs ADAPTORS tu run JOB',
                hint='Either remove your empty entry or setup your classes',
                obj=waves_settings,
                id='waves.wcore.E002',
            )
        )
    elif 'crispy' in settings.INSTALLED_APPS and settings.CRISPY_TEMPLATE_PACK not in waves_settings.TEMPLATES_PACKS:
        errors.append(
            Error(
                'Your crispy template pack is not yet supported in WAVES,',
                hint='Currently, only: %s are supported.' % waves_settings.TEMPLATES_PACKS,
                obj=settings,
                id="waves.wcore.E003"
            )
        )
    return errors
