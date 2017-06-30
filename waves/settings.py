"""
WAVES settings management
These settings may be overridden in your Django main configuration file
"""
from __future__ import unicode_literals

import socket
from importlib import import_module
from os.path import join
from django.conf import settings
from django.test.signals import setting_changed
from django.utils import six

try:
    HOSTNAME = socket.gethostname()
except:
    HOSTNAME = 'localhost'


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    elif isinstance(val, six.string_types):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
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
    'VERSION': __import__('waves').__version__,
    'DB_VERSION': __import__('waves').__db_version__,
    'DATA_ROOT': join(getattr(settings, 'BASE_DIR', '/tmp'), 'data'),
    'JOB_BASE_DIR': join(getattr(settings, 'BASE_DIR', '/tmp'), 'data', 'jobs'),
    'SAMPLE_DIR': join(getattr(settings, 'MEDIA_ROOT', '/tmp'), 'sample'),
    'UPLOAD_MAX_SIZE': 20 * 1024 * 1024,
    'HOST': HOSTNAME,
    'ACCOUNT_ACTIVATION_DAYS': 7,
    'ADMIN_EMAIL': 'admin@atgc-montpellier.fr',
    'ALLOW_JOB_SUBMISSION': True,
    'APP_NAME': 'WAVES',
    'JOBS_MAX_RETRY': 5,
    'KEEP_ANONYMOUS_JOBS': 30,
    'KEEP_REGISTERED_JOBS': 120,
    'NOTIFY_RESULTS': True,
    'REGISTRATION_ALLOWED': True,
    'SERVICES_EMAIL': 'waves@atgc-montpellier.fr',
    'TEMPLATE_PACK': 'bootstrap3',
    'SECRET_KEY': getattr(settings, 'SECRET_KEY', '')[0:32],
    'ADAPTORS_CLASSES': (
        'waves.adaptors.core.shell.SshShellAdaptor',
        'waves.adaptors.core.cluster.LocalClusterAdaptor',
        'waves.adaptors.core.shell.SshKeyShellAdaptor',
        'waves.adaptors.core.shell.LocalShellAdaptor',
        'waves.adaptors.core.cluster.SshClusterAdaptor',
        'waves.adaptors.core.cluster.SshKeyClusterAdaptor',
    ),
    'PERMISSION_CLASSES': (),
    'MAILER_CLASS': 'waves.mails.JobMailer',
    'CATEGORY_CLASS': 'waves.models.services.ServiceCategory'
}

IMPORT_STRINGS = [
    'ADAPTORS_CLASSES',
    'MAILER_CLASS',
    'CATEGORY_CLASS'
]


class WavesSettings(object):
    """
    WAVES settings object, allow WAVES settings access from properties
    """

    def __init__(self, waves_settings=None, defaults=None, imports_string=None):
        if waves_settings:
            self._waves_settings = waves_settings
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
    setting, value = kwargs['setting'], kwargs['value']
    if setting == 'WAVES_CORE':
        waves_settings = WavesSettings(value, DEFAULTS, IMPORT_STRINGS)

setting_changed.connect(reload_waves_settings)
