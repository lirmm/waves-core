""" All WAVES related models imports """
from __future__ import unicode_literals

from waves.wcore.models.adaptors import *
# Automate sub module import
import swapper
from waves.wcore.models.base import *
from waves.wcore.models.history import JobHistory
from waves.wcore.models.runners import *
from waves.wcore.models.binaries import ServiceBinaryFile
from waves.wcore.models.services import *
from waves.wcore.models.inputs import *
from waves.wcore.models.jobs import *
from waves.wcore.models.binaries import ServiceBinaryFile


def get_service_model():
    return swapper.load_model('wcore', 'Service')


def get_submission_model():
    return swapper.load_model('wcore', 'Submission')


"""
List of different constants used for models
"""
OUT_TYPE = (
    ('stout', 'Standard output'),
    ('file', 'Output file')
)
