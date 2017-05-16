"""
Compatibility in case constance is not in installed apps
"""
from __future__ import unicode_literals

import waves.settings


class config(object):
    """ Fake constance config class to enable compatibility in waves files (accessing directly constance config var 
    from config object """
    __dict__ = {'WAVES_ACCOUNT_ACTIVATION_DAYS'}
    pass


config.WAVES_ACCOUNT_ACTIVATION_DAYS = waves.settings.WAVES_ACCOUNT_ACTIVATION_DAYS
config.WAVES_ADMIN_EMAIL = waves.settings.WAVES_ADMIN_EMAIL
config.WAVES_ADMIN_HEADLINE = waves.settings.WAVES_ADMIN_HEADLINE
config.WAVES_ADMIN_TITLE = waves.settings.WAVES_ADMIN_TITLE
config.WAVES_ALLOW_JOB_SUBMISSION = waves.settings.WAVES_ALLOW_JOB_SUBMISSION
config.WAVES_APP_NAME = waves.settings.WAVES_APP_NAME
config.WAVES_APP_VERBOSE_NAME = waves.settings.WAVES_APP_VERBOSE_NAME
config.WAVES_DATA_ROOT = waves.settings.WAVES_DATA_ROOT
config.WAVES_JOB_DIR = waves.settings.WAVES_JOB_DIR
config.WAVES_JOBS_MAX_RETRY = waves.settings.WAVES_JOBS_MAX_RETRY
config.WAVES_KEEP_ANONYMOUS_JOBS = waves.settings.WAVES_KEEP_ANONYMOUS_JOBS
config.WAVES_KEEP_REGISTERED_JOBS = waves.settings.WAVES_KEEP_REGISTERED_JOBS
config.WAVES_NOTIFY_RESULTS = waves.settings.WAVES_NOTIFY_RESULTS
config.WAVES_REGISTRATION_ALLOWED = waves.settings.WAVES_REGISTRATION_ALLOWED
config.WAVES_SAMPLE_DIR = waves.settings.WAVES_SAMPLE_DIR
config.WAVES_SERVICES_EMAIL = waves.settings.WAVES_SERVICES_EMAIL
config.WAVES_UPLOAD_MAX_SIZE = waves.settings.WAVES_UPLOAD_MAX_SIZE
