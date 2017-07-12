""" All WAVES related models imports """
from __future__ import unicode_literals

from django.apps import apps as django_apps
from django.core.exceptions import ImproperlyConfigured

from waves.core.settings import waves_settings
from waves.core.models.adaptors import *
# Automate sub module import
from waves.core.models.base import *
from waves.core.models.history import JobHistory
from waves.core.models.inputs import *
from waves.core.models.jobs import *
from waves.core.models.runners import *
from waves.core.models.samples import *
from waves.core.models.services import *
from waves.core.models.submissions import *

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
        # (self, app_label, model_name=None,
        model = django_apps.get_model(app_label='waves.core',
                                      model_name='Service', require_ready=False)
        print "model", model

        return django_apps.get_model(app_label='waves.core',
                                     model_name='Service', require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("SERVICE_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "SERVICE_MODEL refers to model '%s' that has not been installed" % '.'.join(waves_settings.SERVICE_MODEL)
        )
