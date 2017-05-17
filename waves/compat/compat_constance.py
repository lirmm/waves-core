"""
Set up mandatory constance configuration entries for WAVES
"""
from __future__ import unicode_literals

from os.path import join, dirname

from django.conf import settings
from waves.settings import waves_settings
from waves.compat import list_themes

WAVES_CONSTANCE_CONFIG = {

    'ACCOUNT_ACTIVATION_DAYS': (7, 'Number of days before activation is kept available'),

    'ADMIN_EMAIL': ('admin@atgc-montpellier.fr', 'Waves admin email'),
    'ALLOW_JOB_SUBMISSION': (True, 'Disable job submission (globally)'),
    'APP_NAME': ('WAVES', 'Application name'),
    'DATA_ROOT': (waves_settings.DATA_ROOT, 'Data root dir'),
    'JOB_DIR': (join(waves_settings.JOB_DIR, 'jobs'), 'Job working base dir'),
    'SAMPLE_DIR': (join(dirname(waves_settings.SAMPLE_DIR), 'sample'), 'Sample directory'),

    'JOBS_MAX_RETRY': (5, 'Default retry for failing jobs', int),
    'KEEP_ANONYMOUS_JOBS': (30, 'Number of day to keep anonymous jobs data'),
    'KEEP_REGISTERED_JOBS': (120, 'Number of day to keep registered users jobs data'),
    'NOTIFY_RESULTS': (True, 'Notify results to clients'),
    'REGISTRATION_ALLOWED': (True, 'User registration enabled'),
    'SERVICES_EMAIL': ('waves@atgc-montpellier.fr', 'From email for notification'),
    'UPLOAD_MAX_SIZE': (1024 * 1024 * 20, 'Max uploaded file size'),
}

WAVES_CONSTANCE_CONFIG_FIELDSETS = {
    'Global Options': ('SERVICES_EMAIL', 'ADMIN_EMAIL'),
    'Job Options': ('NOTIFY_RESULTS', 'ALLOW_JOB_SUBMISSION', 'UPLOAD_MAX_SIZE',
                    'JOBS_MAX_RETRY', 'KEEP_ANONYMOUS_JOBS', 'KEEP_REGISTERED_JOBS'),
    'Front Options': ('APP_NAME', 'REGISTRATION_ALLOWED', 'ACCOUNT_ACTIVATION_DAYS'),
}

WAVES_CONSTANCE_ADDITIONAL_FIELDS = {
    'select_theme': ['django.forms.fields.ChoiceField', {
        'widget': 'django.forms.Select',
        'choices': list_themes()
    }],
}

CONSTANCE_CONFIG = getattr(settings, 'CONSTANCE_CONFIG', {})
CONSTANCE_CONFIG.update(WAVES_CONSTANCE_CONFIG)
CONSTANCE_ADDITIONAL_FIELDS = getattr(settings, 'CONSTANCE_ADDITIONAL_FIELDS', {})

CONSTANCE_ADDITIONAL_FIELDS.update(WAVES_CONSTANCE_ADDITIONAL_FIELDS)
CONSTANCE_CONFIG_FIELDSETS = getattr(settings, 'CONSTANCE_CONFIG_FIELDSETS', {})
CONSTANCE_CONFIG_FIELDSETS.update(WAVES_CONSTANCE_CONFIG_FIELDSETS)

settings.CONSTANCE_CONFIG = CONSTANCE_CONFIG
settings.CONSTANCE_ADDITIONAL_FIELDS = CONSTANCE_ADDITIONAL_FIELDS
settings.CONSTANCE_CONFIG_FIELDSETS = CONSTANCE_CONFIG_FIELDSETS
