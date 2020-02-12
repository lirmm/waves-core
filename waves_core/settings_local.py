from .settings import *

""" Dedicated settings for local dev instance """
AUTH_PASSWORD_VALIDATORS = []

# CONF EMAIL
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-messages'
