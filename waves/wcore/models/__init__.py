""" All WAVES related models imports """
from __future__ import unicode_literals

# Automate sub module import
import swapper
from waves.wcore.models.adaptors import AdaptorInitParam, HasAdaptorClazzMixin
from waves.wcore.models.history import JobHistory
from waves.wcore.models.runners import Runner
from waves.wcore.models.binaries import ServiceBinaryFile
from waves.wcore.models.services import SubmissionOutput, SubmissionExitCode
from waves.wcore.models.inputs import AParam, TextParam, BooleanParam, IntegerParam, DecimalParam, ListParam
from waves.wcore.models.jobs import JobOutput, JobInput, Job
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
