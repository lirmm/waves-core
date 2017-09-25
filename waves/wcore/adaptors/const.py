from __future__ import unicode_literals

from collections import namedtuple

from django.utils.translation import ugettext as _

__all__ = [
    'JOB_UNDEFINED',
    'JOB_CREATED',
    'JOB_PREPARED',
    'JOB_QUEUED',
    'JOB_RUNNING',
    'JOB_SUSPENDED',
    'JOB_COMPLETED',
    'JOB_TERMINATED',
    'JOB_CANCELLED',
    'JOB_WARNING',
    'JOB_ERROR',

    'STR_JOB_UNDEFINED',
    'STR_JOB_CREATED',
    'STR_JOB_PREPARED',
    'STR_JOB_QUEUED',
    'STR_JOB_RUNNING',
    'STR_JOB_COMPLETED',
    'STR_JOB_TERMINATED',
    'STR_JOB_CANCELLED',
    'STR_JOB_SUSPENDED',
    'STR_JOB_WARNING',
    'STR_JOB_ERROR',
    'STATUS_LIST',
    'NEXT_STATUS',
    'PENDING_STATUS',
    'STATUS_MAP'
]

#: Undefined status, can be considered as an error status
JOB_UNDEFINED = -1
#: Job has just been created
JOB_CREATED = 0
#: Job is prepared for run
JOB_PREPARED = 1
#: Job is queued on runner adaptor
JOB_QUEUED = 2
#: Job is running
JOB_RUNNING = 3
#: Job has been suspended
JOB_SUSPENDED = 4
#: Job is completed remotly
JOB_COMPLETED = 5
#: Job's data has been retrieved on WAVES platform
JOB_TERMINATED = 6
#: Job has been cancelled
JOB_CANCELLED = 7
#: Job is completed (exit_code is 0), but there is stderr
JOB_WARNING = 8
#: Job is in error
JOB_ERROR = 9

STR_JOB_UNDEFINED = _('Undefined')
STR_JOB_CREATED = _('Created')
STR_JOB_PREPARED = _('Prepared')
STR_JOB_QUEUED = _('Queued')
STR_JOB_RUNNING = _('Running')
STR_JOB_COMPLETED = _('Run completed, pending data retrieval')
STR_JOB_TERMINATED = _('Results data retrieved')
STR_JOB_CANCELLED = _('Cancelled')
STR_JOB_SUSPENDED = _('Suspended')
STR_JOB_WARNING = _('Warnings')
STR_JOB_ERROR = _('Error')

STATUS_LIST = [
    (JOB_UNDEFINED, STR_JOB_UNDEFINED),
    (JOB_CREATED, STR_JOB_CREATED),
    (JOB_PREPARED, STR_JOB_PREPARED),
    (JOB_QUEUED, STR_JOB_QUEUED),
    (JOB_RUNNING, STR_JOB_RUNNING),
    (JOB_SUSPENDED, STR_JOB_SUSPENDED),
    (JOB_COMPLETED, STR_JOB_COMPLETED),
    (JOB_TERMINATED, STR_JOB_TERMINATED),
    (JOB_CANCELLED, STR_JOB_CANCELLED),
    (JOB_WARNING, STR_JOB_WARNING),
    (JOB_ERROR, STR_JOB_ERROR),
]
NEXT_STATUS = {
    JOB_CREATED: JOB_PREPARED,
    JOB_PREPARED: JOB_QUEUED,
    JOB_QUEUED: JOB_RUNNING,
    JOB_RUNNING: JOB_COMPLETED,
    JOB_COMPLETED: JOB_TERMINATED
}
PENDING_STATUS = (JOB_CREATED,
                  JOB_PREPARED,
                  JOB_QUEUED,
                  JOB_RUNNING)

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
JobRunDetails = namedtuple("JobRunDetails",
                           ['id', 'slug', 'job_remote_id', 'name', 'exit_code', 'created', 'started',
                            'finished', 'extra'])
