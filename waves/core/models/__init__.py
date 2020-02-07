""" All WAVES related models imports """

# Automate sub module import
import swapper

from waves.core.models.adaptors import AdaptorInitParam, HasAdaptorClazzMixin
from waves.core.models.binaries import ServiceBinaryFile
from waves.core.models.history import JobHistory
from waves.core.models.inputs import AParam, TextParam, BooleanParam, IntegerParam, DecimalParam, ListParam
from waves.core.models.jobs import JobOutput, JobInput, Job
from waves.core.models.runners import Runner
from waves.core.models.services import Submission, SubmissionOutput, SubmissionExitCode, BaseService, BaseSubmission


def get_service_model() -> BaseService:
    return swapper.load_model('waves', 'Service')


def get_submission_model() -> BaseSubmission:
    return swapper.load_model('waves', 'Submission')


"""
List of different constants used for models
"""
OUT_TYPE = (
    ('stout', 'Standard output'),
    ('file', 'Output file')
)
