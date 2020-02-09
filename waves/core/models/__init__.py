""" All WAVES related models imports """
from waves.core.models.adaptors import AdaptorInitParam, HasAdaptorClazzMixin
from waves.core.models.binaries import ServiceBinaryFile
from waves.core.models.history import JobHistory
from waves.core.models.inputs import AParam, TextParam, BooleanParam, IntegerParam, DecimalParam, ListParam
from waves.core.models.jobs import JobOutput, JobInput, Job
from waves.core.models.runners import Runner
from waves.core.models.services import Submission, SubmissionOutput, SubmissionExitCode, Service

"""
List of different constants used for models
"""
OUT_TYPE = (
    ('stout', 'Standard output'),
    ('file', 'Output file')
)
