""" All WAVES related models imports """
from __future__ import unicode_literals

# Automate sub module import
from django.apps import apps as django_apps
from django.core.exceptions import ImproperlyConfigured
from waves.models.base import *
from waves.models.adaptors import *
from waves.models.runners import *
from waves.models.services import *
from waves.models.jobs import *
from waves.models.submissions import *
from waves.models.inputs import *
from waves.models.samples import *
from waves.models.history import JobHistory
from waves.settings import waves_settings

"""
List of different constants used for models
"""
OUT_TYPE = (
    ('stout', 'Standard output'),
    ('file', 'Output file')
)


def get_service_model():
    """
    Returns the User model that is active in this project.
    """
    try:
        return django_apps.get_model(waves_settings.SERVICE_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("SERVICE_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "AUTH_USER_MODEL refers to model '%s' that has not been installed" % waves_settings.SERVICE_MODEL
        )
