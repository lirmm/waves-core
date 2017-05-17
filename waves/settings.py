"""
WAVES proprietary optional settings
These settings may be overridden in your Django main configuration file
"""
from __future__ import unicode_literals

from os.path import join

from django.conf import settings

from . import __version__

WAVES_VERSION = __version__
WAVES_DATA_ROOT = getattr(settings, 'WAVES_DATA_ROOT', join(settings.BASE_DIR, 'data'))
WAVES_JOB_DIR = getattr(settings, 'WAVES_JOB_DIR', join(WAVES_DATA_ROOT, 'jobs'))
WAVES_SAMPLE_DIR = getattr(settings, 'WAVES_SAMPLE_DIR', join(settings.MEDIA_ROOT, 'sample'))
WAVES_UPLOAD_MAX_SIZE = getattr(settings, 'WAVES_UPLOAD_MAX_SIZE', 20 * 1024 * 1024)
WAVES_HOST = getattr(settings, 'WAVES_HOST', 'http://localhost')

WAVES_ACCOUNT_ACTIVATION_DAYS = getattr(settings, 'WAVES_ACCOUNT_ACTIVATION_DAYS', 7)
WAVES_ADMIN_EMAIL = getattr(settings, 'WAVES_ADMIN_EMAIL', 'admin@atgc-montpellier.fr')
WAVES_ADMIN_HEADLINE = getattr(settings, 'WAVES_ADMIN_HEADLINE', "Waves")
WAVES_ADMIN_TITLE = getattr(settings, 'WAVES_ADMIN_TITLE', 'WAVES Administration')
WAVES_ALLOW_JOB_SUBMISSION = getattr(settings, 'WAVES_ALLOW_JOB_SUBMISSION', True)
WAVES_APP_NAME = getattr(settings, 'WAVES_APP_NAME', 'WAVES')
WAVES_APP_VERBOSE_NAME = getattr(settings, 'WAVES_APP_VERBOSE_NAME',
                                 'Web Application for Versatile & Easy bioinformatics Services')
WAVES_JOBS_MAX_RETRY = getattr(settings, 'WAVES_JOBS_MAX_RETRY', 5)
WAVES_KEEP_ANONYMOUS_JOBS = getattr(settings, 'WAVES_KEEP_ANONYMOUS_JOBS', 30)
WAVES_KEEP_REGISTERED_JOBS = getattr(settings, 'WAVES_KEEP_REGISTERED_JOBS', 120)
WAVES_NOTIFY_RESULTS = getattr(settings, 'WAVES_NOTIFY_RESULTS', True)
WAVES_REGISTRATION_ALLOWED = getattr(settings, 'WAVES_REGISTRATION_ALLOWED', True)
WAVES_SERVICES_EMAIL = getattr(settings, 'WAVES_SERVICES_EMAIL', 'waves@atgc-montpellier.fr')
WAVES_TEMPLATE_PACK = getattr(settings, 'CRISPY_TEMPLATE_PACK', 'bootstrap3')

WAVES_ADAPTORS_CLASSES = getattr(settings, 'WAVES_ADAPTORS_CLASSES', [
    'waves.adaptors.core.shell.SshShellAdaptor',
    'waves.adaptors.core.cluster.LocalClusterAdaptor',
    'waves.adaptors.core.shell.SshKeyShellAdaptor',
    'waves.adaptors.core.shell.LocalShellAdaptor',
    'waves.adaptors.core.cluster.SshClusterAdaptor',
    'waves.adaptors.core.cluster.SshKeyClusterAdaptor',
])
