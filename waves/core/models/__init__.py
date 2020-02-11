""" All WAVES related models imports """
from waves.core.models.binaries import *
from waves.core.models.services import *
from waves.core.models.adaptors import *
from waves.core.models.runners import *
from waves.core.models.history import *
from waves.core.models.inputs import *
from waves.core.models.jobs import *

"""
List of different constants used for models
"""
OUT_TYPE = (
    ('stout', 'Standard output'),
    ('file', 'Output file')
)
