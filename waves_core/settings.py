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

from django.contrib import messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add custom path for RADICAL state storage
# https://github.com/radical-cybertools/radical.utils/blob/devel/src/radical/utils/misc.py @739
# os.environ['RADICAL_BASE'] = os.path.join(BASE_DIR)
os.environ["RADICAL_BASE"] = "/var/www/html/waves/data"
# distant directory for sync files
os.environ["RADICAL_BASE_TGT"] = "/auto/alimouzinlamothe"
os.environ["RADICAL_SAGA_LOG_TGT"] = os.path.join(os.environ["RADICAL_BASE"], "logs/radical.saga.log")
os.environ["RADICAL_UTILS_LOG_TGT"] = os.path.join(os.environ["RADICAL_BASE"], "logs/radical.utils.log")
# os.environ["RADICAL_CONFIG_USER_DIR"] = os.environ["RADICAL_BASE"]
os.environ["RADICAL_LOG_LVL"] = 'DEBUG'

# from radical.saga.utils.config import getConfig
# sagaconf = getConfig()
# pprint.pprint(ru.Config('radical.saga.log'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "SECRET_KEY", "0jmf=ngd^2**h3km5@#&w21%hlj9kos($2=igsqh8-38_9g1$1"
)

# SECURITY WARNING: switch lines in prod
DEBUG = True
# DEBUG = os.getenv('DEBUG', 'False') == "True"
# DEBUG : INTERNAL_IPS required for debug toolbar
INTERNAL_IPS = ["127.0.0.1"]

ALLOWED_HOSTS = ["waves.local"]

# Application definition
INSTALLED_APPS = [
    "polymorphic",
    # STANDARD DJANGO
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # WAVES CORE
    "waves",
    "waves.api",
    # 'waves.wcore',
    "waves.authentication",
    "crispy_forms",
    "rest_framework",
    'drf_spectacular',
    "corsheaders",
    "adminsortable2",
    # Check if needed
    "django_sb_admin",
    "debug_toolbar",
    "django_crontab",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

ROOT_URLCONF = "waves_core.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
            "builtins": ["material.templatetags.material_form", ],
        },
    },
]

WSGI_APPLICATION = "waves_core.wsgi.application"

# DATABASE configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR + "/db.sqlite3",
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator", },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator", },
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator", },
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"
MEDIA_ROOT = os.path.join(BASE_DIR, "data/media")
MEDIA_URL = "/media/"

STATICFILES_DIRS = [os.path.join(BASE_DIR, "waves/static")]

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

CRISPY_TEMPLATE_PACK = "bootstrap3"

SPECTACULAR_SETTINGS = {
    'TITLE': 'Waves API',
    'DESCRIPTION': 'Autogenerated API Endpoint to interact with distant computing infrastructure',
    'VERSION': '0.1.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # 'SCHEMA_PATH_PREFIX': '/api/',
    # 'SERVERS': [{'url' : 'http://waves.local/', 'description': 'Local test server' }]
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "waves.authentication.auth.TokenAuthentication",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FileUploadParser",
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
ALLOWED_TEMPLATE_PACKS = ["bootstrap3", "bootstrap4"]

MESSAGE_TAGS = {messages.ERROR: "error"}

# SECURITY
CORS_ORIGIN_WHITELIST = ("http://localhost", "http://127.0.0.1")
CORS_ORIGIN_REGEX_WHITELIST = ["localhost:*"]
CORS_ORIGIN_ALLOW_ALL = True

FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
FILE_UPLOAD_PERMISSIONS = 0o775

# EMAILS
DEFAULT_FROM_EMAIL = "WAVES <waves-demo@atgc-montpellier.fr>"
CONTACT_EMAIL = DEFAULT_FROM_EMAIL

# CONF EMAIL
# FIXME mode to SMTP or env value
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = "/tmp/app-messages"  # change this to a proper location

MANAGERS = [("Vincent Lefort", "vincent.lefort@lirmm.fr")]
LOG_DIR = os.path.join(BASE_DIR, "data/logs")
APP_LOG_LEVEL = "WARNING"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(levelname)s][%(asctime)s][%(name)s.%(funcName)s:%(lineno)s] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "log_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "waves-app.log"),
            "formatter": "verbose",
            "backupCount": 10,
            "maxBytes": 1024 * 1024 * 5,
        },
    },
    "loggers": {
        "django": {"handlers": ["log_file"], "propagate": True, "level": "ERROR", },
        "waves": {"handlers": ["log_file"], "level": "DEBUG", "propagate": True, },
        "rest_framework.request": {
            "handlers": ["log_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django_crontab": {
            "handlers": ["log_file"],
            "propagate": True,
            "level": "DEBUG",
        },
        "waves.cron": {
            "handlers": ["log_file"],
            "propagate": False,
            "level": "DEBUG",
        },
        "saga": {},
    },
}

# Without Celery Add thoses and run manage.py crontab add
CRONJOBS = [
    ("0 * * * *", "waves.core.cron.process_job_queue"),
    ("0 * * * *", "waves.core.cron.purge_old_jobs"),
]

# Broker configuration for celery
URL_BROKER = "redis://localhost:6379"
