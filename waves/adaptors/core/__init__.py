"""
WAVES runner adaptor module
"""
from __future__ import unicode_literals

## Avoid user warning for logging init
import saga
## //
from collections import namedtuple

__author__ = "Marc Chakiachvili <marc.chakiachvili@lirmm.fr>"
__version__ = "1.0"
__group__ = "Core WAVES Adaptor"

""" Constants used for jobs """
JOB_UNDEFINED   = -1
JOB_CREATED     = 0
JOB_PREPARED    = 1
JOB_QUEUED      = 2
JOB_RUNNING     = 3
JOB_SUSPENDED   = 4
JOB_COMPLETED   = 5
JOB_TERMINATED  = 6
JOB_CANCELLED   = 7
JOB_ERROR       = 9

STR_JOB_UNDEFINED   = 'Unknown'
STR_JOB_CREATED     = 'Created'
STR_JOB_PREPARED    = 'Prepared for run'
STR_JOB_QUEUED      = 'Queued'
STR_JOB_RUNNING     = 'Running'
STR_JOB_COMPLETED   = 'Run completed'
STR_JOB_TERMINATED  = 'Finished'
STR_JOB_CANCELLED   = 'Cancelled'
STR_JOB_SUSPENDED   = 'Suspended'
STR_JOB_ERROR       = 'In Error'


JobRunDetails = namedtuple("JobRunDetails",
                           ['id', 'slug', 'job_remote_id', 'name', 'exit_code', 'created', 'started',
                            'finished', 'extra'])

STATUS_MAP = {
    JOB_UNDEFINED: STR_JOB_UNDEFINED,
    JOB_CREATED: STR_JOB_CREATED,
    JOB_PREPARED: STR_JOB_PREPARED,
    JOB_QUEUED: STR_JOB_QUEUED,
    JOB_RUNNING: STR_JOB_RUNNING,
    JOB_SUSPENDED: STR_JOB_SUSPENDED,
    JOB_COMPLETED: STR_JOB_COMPLETED,
    JOB_TERMINATED: STR_JOB_TERMINATED,
    JOB_CANCELLED: STR_JOB_CANCELLED,
    JOB_ERROR: STR_JOB_ERROR,
}