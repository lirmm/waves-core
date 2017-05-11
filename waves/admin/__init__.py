""" Models admin packages """
from django.conf import settings

from waves.admin.jobs import *
from waves.admin.runners import *
from waves.admin.services import *
from waves.admin.submissions import SubmissionOutputInline, ExitCodeInline, SampleDependentInputInline, \
    FileInputSampleInline
from waves.admin.inputs import *
from waves.admin.config import *