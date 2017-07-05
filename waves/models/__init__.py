""" All WAVES related models imports """
from __future__ import unicode_literals

# Automate sub module import
from waves.models.base import *
from waves.models.adaptors import *
from waves.models.runners import *
from waves.models.services import *
from waves.models.jobs import *
from waves.models.submissions import *
from waves.models.inputs import *
from waves.models.samples import *
from waves.models.history import JobHistory

"""
List of different constants used for models
"""
OUT_TYPE = (
    ('stout', 'Standard output'),
    ('file', 'Output file')
)
