""" All WAVES related models imports """
from __future__ import unicode_literals

from waves.wcore.models.adaptors import *
# Automate sub module import
from waves.wcore.models.base import *
from waves.wcore.models.history import JobHistory
from waves.wcore.models.inputs import *
from waves.wcore.models.jobs import *
from waves.wcore.models.runners import *
from waves.wcore.models.services import *

"""
List of different constants used for models
"""
OUT_TYPE = (
    ('stout', 'Standard output'),
    ('file', 'Output file')
)
