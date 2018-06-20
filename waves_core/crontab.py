from __future__ import unicode_literals


import warnings

from waves_core.settings import *

try:
    from django_crontab import *
except ImportError:
    warnings.warn("Please install django_crontab package")
    exit(1)

CLI_LOG_LEVEL = 'WARNING'

INSTALLED_APPS += [
    'django_crontab'
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s][%(asctime)s][%(name)s.%(funcName)s:%(lineno)s] - %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'log_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'waves-cli.log'),
            'formatter': 'verbose',
            'backupCount': 10,
            'maxBytes': 1024 * 1024 * 5
        },
    },

    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'WARNING',
        },
        'waves': {
            'handlers': ['log_file'],
            'level': CLI_LOG_LEVEL,
            'propagate': True,
        },
        'django_crontab': {
            'handlers': ['log_file'],
            'propagate': True,
            'level': CLI_LOG_LEVEL,
        },
        'waves.daemon': {
            'handlers': ['log_file'],
            'propagate': False,
            'level': 'INFO',
        },
        'daemons': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'INFO',
        },

    }
}

# CRONTAB JOBS
CRONTAB_COMMAND_SUFFIX = '2>&1'
CRONTAB_COMMAND_PREFIX = ''
CRONTAB_DJANGO_SETTINGS_MODULE = 'waves_core.crontab'
CRONTAB_LOCK_JOBS = True
CRONJOBS = [
    ('*/5 * * * *', 'django.core.management.call_command', ['wqueue', 'start']),
    ('0 * * * *', 'django.core.management.call_command', ['wpurge', 'start']),
]
