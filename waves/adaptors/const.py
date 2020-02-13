from collections import namedtuple


__all__ = ['JobStatus', 'JobRunDetails']


class JobStatus(object):
    #: Undefined status, usually an job init error status
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
    #: Job is completed remotely
    JOB_COMPLETED = 5
    #: Job's data has been retrieved on WAVES platform
    JOB_FINISHED = 6
    #: Job has been cancelled
    JOB_CANCELLED = 7
    #: Job is completed (exit_code is 0), but there is stderr
    JOB_WARNING = 8
    #: Job execution show errors
    JOB_ERROR = 9

    STR_JOB_UNDEFINED = 'Undefined'
    STR_JOB_CREATED = 'Created'
    STR_JOB_PREPARED = 'Prepared'
    STR_JOB_QUEUED = 'Queued'
    STR_JOB_RUNNING = 'Running'
    STR_JOB_COMPLETED = 'Run completed, pending data retrieval'
    STR_JOB_FINISHED = 'Results data retrieved'
    STR_JOB_CANCELLED = 'Cancelled'
    STR_JOB_SUSPENDED = 'Suspended'
    STR_JOB_WARNING = 'Warnings'
    STR_JOB_ERROR = 'Error'

    STATUS_LIST = [
        (JOB_UNDEFINED, STR_JOB_UNDEFINED),
        (JOB_CREATED, STR_JOB_CREATED),
        (JOB_PREPARED, STR_JOB_PREPARED),
        (JOB_QUEUED, STR_JOB_QUEUED),
        (JOB_RUNNING, STR_JOB_RUNNING),
        (JOB_SUSPENDED, STR_JOB_SUSPENDED),
        (JOB_COMPLETED, STR_JOB_COMPLETED),
        (JOB_FINISHED, STR_JOB_FINISHED),
        (JOB_CANCELLED, STR_JOB_CANCELLED),
        (JOB_WARNING, STR_JOB_WARNING),
        (JOB_ERROR, STR_JOB_ERROR),
    ]
    NEXT_STATUS = {
        JOB_CREATED: JOB_PREPARED,
        JOB_PREPARED: JOB_QUEUED,
        JOB_QUEUED: JOB_RUNNING,
        JOB_RUNNING: JOB_COMPLETED,
        JOB_COMPLETED: JOB_FINISHED
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
        JOB_FINISHED: STR_JOB_FINISHED,
        JOB_CANCELLED: STR_JOB_CANCELLED,
        JOB_ERROR: STR_JOB_ERROR,
    }


JobRunDetails = namedtuple("JobRunDetails",
                           ['id', 'slug', 'job_remote_id', 'name', 'exit_code', 'created', 'started',
                            'finished', 'extra'])
