"""
Django settings for waves_core project.

Generated by 'django-admin startproject' using Django 1.11.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""
from __future__ import unicode_literals

import logging.config
import os

from django.contrib import messages

# python 3 compatibility
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

from django.conf import settings
from os.path import join, isfile

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '0jmf=ngd^2**h3km5@#&w21%hlj9kos($2=igsqh8-38_9g1$1'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'polymorphic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'waves.wcore',
    'waves.authentication',
    'crispy_forms',
    'rest_framework',
    'corsheaders',
    'adminsortable2',
    'django_crontab'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'waves_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'waves_core.wsgi.application'

# DATABASE configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR + '/db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'data/media')
MEDIA_URL = "/media/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "waves", "wcore", "static"),
    os.path.join(BASE_DIR, "static")
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

CRISPY_TEMPLATE_PACK = 'bootstrap3'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'waves.authentication.auth.TokenAuthentication',
        'waves.authentication.auth.ApiKeyAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser',
        'rest_framework.parsers.JSONParser',

    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.CoreJSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',

    )
}
ALLOWED_TEMPLATE_PACKS = ['bootstrap3', 'bootstrap4']

MESSAGE_TAGS = {
    messages.ERROR: 'error'
}

# SECURITY
CORS_ORIGIN_WHITELIST = 'localhost'
CORS_ORIGIN_REGEX_WHITELIST = ['localhost:*']
CORS_ORIGIN_ALLOW_ALL = True

FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
FILE_UPLOAD_PERMISSIONS = 0o775

# EMAILS
DEFAULT_FROM_EMAIL = 'WAVES <waves-demo@atgc-montpellier.fr>'
CONTACT_EMAIL = DEFAULT_FROM_EMAIL

# WAVES
ADAPTORS_DEFAULT_CLASSES = (
    'waves.wcore.adaptors.shell.SshShellAdaptor',
    'waves.wcore.adaptors.cluster.LocalClusterAdaptor',
    'waves.wcore.adaptors.shell.SshKeyShellAdaptor',
    'waves.wcore.adaptors.shell.LocalShellAdaptor',
    'waves.wcore.adaptors.cluster.SshClusterAdaptor',
    'waves.wcore.adaptors.cluster.SshKeyClusterAdaptor',
)
WAVES_CORE = {
    'ACCOUNT_ACTIVATION_DAYS': 14,
    'ADMIN_EMAIL': 'admin@waves.atgc-montpellier.fr',
    'DATA_ROOT': os.path.join(BASE_DIR, 'data'),
    'JOB_LOG_LEVEL': logging.DEBUG,
    'JOB_BASE_DIR': os.path.join(BASE_DIR, 'data', 'jobs'),
    'BINARIES_DIR': os.path.join(BASE_DIR, 'data', 'bin'),
    'SAMPLE_DIR': os.path.join(BASE_DIR, 'data', 'sample'),
    'KEEP_ANONYMOUS_JOBS': 2,
    'KEEP_REGISTERED_JOBS': 30,
    'ALLOW_JOB_SUBMISSION': True,
    'APP_NAME': 'WAVES CORE',
    'SERVICES_EMAIL': 'contact@waves.atgc-montpellier.fr',
    'ADAPTORS_CLASSES': ADAPTORS_DEFAULT_CLASSES,
}

# CONF EMAIL
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-messages'  # change this to a proper location

MANAGERS = [('Vincent Lefort', 'vincent.lefort@lirmm.fr')]
LOG_DIR = os.path.join(BASE_DIR, 'data/logs')
APP_LOG_LEVEL = 'WARNING'
TEST_DATA_ROOT = os.path.join(BASE_DIR, "tests", 'data')

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
            'filename': os.path.join(LOG_DIR, 'waves-app.log'),
            'formatter': 'verbose',
            'backupCount': 10,
            'maxBytes': 1024 * 1024 * 5
        },
    },

    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'ERROR',
        },
        'waves': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'rest_framework.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

configFile = join(BASE_DIR, 'tests', 'settings.ini')

try:
    assert (isfile(configFile))
    Config = ConfigParser.SafeConfigParser()
    Config.read(configFile)
    WAVES_TEST_SSH_HOST = Config.get('saga', 'WAVES_TEST_SSH_HOST')
    WAVES_TEST_SSH_USER_ID = Config.get('saga', 'WAVES_TEST_SSH_USER_ID')
    WAVES_TEST_SSH_USER_PASS = Config.get('saga', 'WAVES_TEST_SSH_USER_PASS')
    WAVES_TEST_SSH_BASE_DIR = Config.get('saga', 'WAVES_TEST_SSH_BASE_DIR')

    WAVES_LOCAL_TEST_SGE_CELL = Config.get('sge_cluster', 'WAVES_LOCAL_TEST_SGE_CELL')
    WAVES_SSH_TEST_SGE_CELL = Config.get('sge_cluster', 'WAVES_SSH_TEST_SGE_CELL')
    WAVES_SSH_TEST_SGE_BASE_DIR = Config.get('sge_cluster', 'WAVES_SSH_TEST_SGE_BASE_DIR')

    WAVES_SSH_KEY_USER_ID = Config.get('ssh_key_cluster', 'WAVES_SSH_KEY_USER_ID')
    WAVES_SSH_KEY_HOST = Config.get('ssh_key_cluster', 'WAVES_SSH_KEY_HOST')
    WAVES_SSH_KEY_PASSPHRASE = Config.get('ssh_key_cluster', 'WAVES_SSH_KEY_PASSPHRASE')
    WAVES_SSH_KEY_BASE_DIR = Config.get('ssh_key_cluster', 'WAVES_SSH_KEY_BASE_DIR')

    WAVES_SLURM_TEST_SSH_HOST = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_HOST')
    WAVES_SLURM_TEST_SSH_USER_ID = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_USER_ID')
    WAVES_SLURM_TEST_SSH_USER_PASS = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_USER_PASS')
    WAVES_SLURM_TEST_SSH_QUEUE = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_QUEUE')
    WAVES_SLURM_TEST_SSH_BASE_DIR = Config.get('slurm_cluster', 'WAVES_SLURM_TEST_SSH_BASE_DIR')
except AssertionError:
    # Don't load variables from ini files they are initialized elsewhere (i.e lab ci)
    pass

# CRONTAB JOBS
CRONTAB_COMMAND_SUFFIX = '2>&1'
CRONTAB_COMMAND_PREFIX = ''
CRONTAB_DJANGO_SETTINGS_MODULE = 'waves_core.crontab'
CRONTAB_LOCK_JOBS = True
CRONJOBS = [
    ('* * * * *', 'waves.wcore.cron.process_job_queue'),
    ('*/10 * * * *', 'waves.wcore.cron.purge_old_jobs')
]
