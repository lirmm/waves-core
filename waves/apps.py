"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the GNU GPL v3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       https://www.gnu.org/licenses/gpl-3.0.en.html
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import os
from os import access

from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Error, register, Warning


# noinspection PyUnresolvedReferences
class WavesConfig(AppConfig):
    """
    WAVES main application AppConfig, add signals for waves_webapp
    """
    name = 'waves'
    verbose_name = 'WAVES CORE'

    def ready(self):
        """
        Executed once when WAVES application startup !
        Just import waves signals
        :return: None
        """
        super().ready()
        import waves.signals


@register()
def check_waves_config(app_configs=('waves',), **kwargs):
    """
    WAVES configuration check up, added to classic ``manage.py check`` Django command

    :param app_configs:
    :param kwargs:
    :return:
    """
    errors = []
    # check values for SECRET_KEY
    from waves.settings import waves_settings
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
                id='waves.core.E001',
            )
        )
    elif len(waves_settings.ADAPTORS_CLASSES) == 0:
        errors.append(
            Error(
                'You set ADAPTORS_CLASSES but empty, WAVES needs ADAPTORS tu run JOB',
                hint='Either remove your empty entry or setup your classes',
                obj=waves_settings,
                id='waves.core.E002',
            )
        )
    elif 'crispy' in settings.INSTALLED_APPS and settings.CRISPY_TEMPLATE_PACK not in waves_settings.TEMPLATES_PACKS:
        errors.append(
            Error(
                'Your crispy template pack is not yet supported in WAVES,',
                hint='Currently, only: %s are supported.' % waves_settings.TEMPLATES_PACKS,
                obj=settings,
                id="waves.core.E003"
            )
        )
    from waves.settings import waves_settings
    # test log dir
    # Test WAVES DIR
    for directory in ['DATA_ROOT', 'JOB_BASE_DIR', 'BINARIES_DIR', 'SAMPLE_DIR']:
        if not os.path.isdir(getattr(waves_settings, directory)):
            errors.append(Error(
                "Directory %s [%s] does not exists " % (directory, getattr(waves_settings, directory)),
                hint='Create this directory with group permission for your WAVES daemon system user',
                obj=waves_settings,
                id="waves.core.E004"))
        elif not access(getattr(waves_settings, directory), os.W_OK):
            errors.append(Warning(
                "Directory %s [%s] is not writable by WAVES" % (directory, getattr(waves_settings, directory)),
                hint='Try changing group permission to a group where your user belong',
                obj=waves_settings,
                id="waves.core.W001"))

    return errors
