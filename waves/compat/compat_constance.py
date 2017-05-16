"""
Set up mandatory constance configuration entries for WAVES
"""
from __future__ import unicode_literals

from os.path import join, dirname

from django.conf import settings
import waves.settings
from waves.compat import list_themes

WAVES_CONSTANCE_CONFIG = {

    'WAVES_ACCOUNT_ACTIVATION_DAYS': (7, 'Number of days before activation is kept available'),

    'WAVES_ADMIN_EMAIL': ('admin@atgc-montpellier.fr', 'Waves admin email'),
    'WAVES_ALLOW_JOB_SUBMISSION': (True, 'Disable job submission (globally)'),
    'WAVES_APP_NAME': ('WAVES', 'Application name'),
    'WAVES_APP_VERBOSE_NAME': ('Web Application for Versatile & Easy bioinformatics Services',
                               'Application verbose name'),
    'WAVES_DATA_ROOT': (waves.settings.WAVES_DATA_ROOT, 'Data root dir'),
    'WAVES_JOB_DIR': (join(waves.settings.WAVES_JOB_DIR, 'jobs'), 'Job working base dir'),
    'WAVES_SAMPLE_DIR': (join(dirname(waves.settings.WAVES_SAMPLE_DIR), 'sample'), 'Sample directory'),

    'WAVES_JOBS_MAX_RETRY': (5, 'Default retry for failing jobs', int),
    'WAVES_KEEP_ANONYMOUS_JOBS': (30, 'Number of day to keep anonymous jobs data'),
    'WAVES_KEEP_REGISTERED_JOBS': (120, 'Number of day to keep registered users jobs data'),
    'WAVES_NOTIFY_RESULTS': (True, 'Notify results to clients'),
    'WAVES_REGISTRATION_ALLOWED': (True, 'User registration enabled'),
    'WAVES_SERVICES_EMAIL': ('waves@atgc-montpellier.fr', 'From email for notification'),
    'WAVES_UPLOAD_MAX_SIZE': (1024 * 1024 * 20, 'Max uploaded file size'),
}

WAVES_CONSTANCE_CONFIG_FIELDSETS = {
    'Global Options': ('WAVES_SERVICES_EMAIL', 'WAVES_ADMIN_EMAIL'),
    'Job Options': ('WAVES_NOTIFY_RESULTS', 'WAVES_ALLOW_JOB_SUBMISSION', 'WAVES_UPLOAD_MAX_SIZE',
                    'WAVES_JOBS_MAX_RETRY', 'WAVES_KEEP_ANONYMOUS_JOBS', 'WAVES_KEEP_REGISTERED_JOBS'),
    'Front Options': ('WAVES_APP_NAME', 'WAVES_APP_VERBOSE_NAME',
                      'WAVES_REGISTRATION_ALLOWED', 'WAVES_ACCOUNT_ACTIVATION_DAYS'),
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
