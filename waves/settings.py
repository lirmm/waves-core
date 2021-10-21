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

import logging
import socket
from importlib import import_module
from os.path import join

import six
from django.conf import settings
from django.test.signals import setting_changed

from waves import __version__, __db_version__

try:
    HOSTNAME = socket.gethostname()
except socket.error:
    HOSTNAME = 'localhost'


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    elif isinstance(val, six.string_types):
        return import_from_string(val)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item) for item in val]
    return val


def import_from_string(val):
    """
    Attempt to import a class from a string representation.
    """
    try:
        parts = val.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        msg = "Could not import '%s' for WAVES settings '%s': %s." % (val, e.__class__.__name__, e)
        raise ImportError(msg)


DEFAULTS = {
    'VERSION': __version__,
    'DB_VERSION': __db_version__,
    'DATA_ROOT': join(getattr(settings, 'BASE_DIR', '/tmp'), 'data'),
    'JOB_BASE_DIR': join(getattr(settings, 'BASE_DIR', '/tmp'), 'data', 'jobs'),
    'BINARIES_DIR': join(getattr(settings, 'BASE_DIR', '/tmp'), 'data', 'bin'),
    'SAMPLE_DIR': join(getattr(settings, 'BASE_DIR', '/tmp'), 'data', 'sample'),
    'UPLOAD_MAX_SIZE': 20 * 1024 * 1024,
    'HOST': HOSTNAME,
    'ADMIN_EMAIL': 'admin@your-site.com',
    'ALLOW_JOB_SUBMISSION': True,
    'APP_NAME': 'WAVES',
    'JOBS_MAX_RETRY': 5,
    'JOB_LOG_LEVEL': logging.INFO,
    'SRV_IMPORT_LOG_LEVEL': logging.INFO,
    'KEEP_ANONYMOUS_JOBS': 30,
    'KEEP_REGISTERED_JOBS': 120,
    'NOTIFY_RESULTS': True,
    'REGISTRATION_ALLOWED': True,
    'SERVICES_EMAIL': 'waves@atgc-montpellier.fr',
    'TEMPLATE_PACK': getattr(settings, 'CRISPY_TEMPLATE_PACK', 'bootstrap3'),
    'SECRET_KEY': getattr(settings, 'SECRET_KEY', '')[0:32],
    'ADAPTORS_CLASSES': (
        'waves.core.adaptors.saga.shell.SshShellAdaptor',
        'waves.core.adaptors.saga.cluster.LocalClusterAdaptor',
        'waves.core.adaptors.saga.shell.SshKeyShellAdaptor',
        'waves.core.adaptors.saga.shell.LocalShellAdaptor',
        'waves.core.adaptors.saga.cluster.SshClusterAdaptor',
        'waves.core.adaptors.saga.cluster.SshKeyClusterAdaptor',
    ),
    'PURGE_WAIT': 86400,
    'PERMISSION_CLASSES': (),
    'MAILER_CLASS': 'waves.mails.JobMailer',
}

TEMPLATES_PACKS = ['bootstrap3', 'bootstrap2'],

IMPORT_STRINGS = [
    'ADAPTORS_CLASSES',
    'MAILER_CLASS',
]


def get_db_version():
    return waves_settings.DB_VERSION


class WavesSettings(object):
    """
    WAVES settings object, allow WAVES settings access from properties
    """

    def __init__(self, waves_up_settings=None, defaults=None, imports_string=None):
        if waves_up_settings:
            self._waves_settings = waves_up_settings
        self.defaults = defaults or DEFAULTS
        self.import_strings = imports_string or IMPORT_STRINGS

    @property
    def waves_settings(self):
        if not hasattr(self, '_waves_settings'):
            self._waves_settings = getattr(settings, 'WAVES_CORE', {})
        return self._waves_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid WAVES setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.waves_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        # Cache the result
        setattr(self, attr, val)
        return val

    def dump_config(self):
        return sorted([(key, getattr(self, key, self.defaults[key])) for key in self.defaults.keys()])


waves_settings = WavesSettings(None, DEFAULTS, IMPORT_STRINGS)


def reload_waves_settings(*args, **kwargs):
    global waves_settings
    setting, value = kwargs.get('setting'), kwargs.get('value')
    if setting == 'WAVES_CORE':
        waves_settings = WavesSettings(value, DEFAULTS, IMPORT_STRINGS)


setting_changed.connect(reload_waves_settings)
