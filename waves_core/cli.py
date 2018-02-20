from __future__ import unicode_literals

from waves_core.settings import *
from os.path import join, dirname

LOGGING_CONFIG = None

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'waves_log_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': join(BASE_DIR, 'logs', 'daemon.log'),
            'formatter': 'simple',
            'backupCount': 10,
            'maxBytes': 50000
        },
    },
    'loggers': {
        'root': {
            'handlers': ['waves_log_file', 'console'],
            'propagate': False,
            'level': 'ERROR',
        },
        'radical.saga': {
            'handlers': ['waves_log_file'],
            'level': 'WARNING',
        },
        'waves': {
            'handlers': ['waves_log_file'],
            'level': 'ERROR',
        },
        'waves.daemon': {
            'handlers': ['waves_log_file'],
            'propagate': True,
            'level': 'INFO',
        },
        'daemons.django.wcore': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },

    }
}
logging.config.dictConfig(LOGGING)
