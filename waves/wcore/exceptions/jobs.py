from __future__ import unicode_literals

from waves.wcore.exceptions import WavesException

__all__ = ['JobException', 'JobRunException', 'JobSubmissionException', 'JobCreateException',
           'JobMissingMandatoryParam', 'JobInconsistentStateError', 'JobPrepareException']


class JobException(WavesException):
    """ Base Exception class for all job related errors  """

    def __init__(self, message, job=None):
        if job:
            self.message = '[job:%s][%s] - %s' % (job.slug, job.remote_job_id, message)
        super(JobException, self).__init__(message)


class JobRunException(JobException):
    """ Job 'run' generic error parent class """
    pass


class JobSubmissionException(JobException):
    """ Job submission generic error parent class """
    pass


class JobCreateException(JobSubmissionException):
    """ Job creation process erro """

    def __init__(self, message, job=None):
        super(JobException, self).__init__(message)


class JobMissingMandatoryParam(JobSubmissionException):
    """ Inconsistency in job submission detected, missing a required params to run job (issued from service
    configuration """

    def __init__(self, param, job):
        message = u'Missing mandatory parameter "%s"' % param
        super(JobMissingMandatoryParam, self).__init__(message, job)


class JobInconsistentStateError(JobRunException):
    """ Inconsistency detected in job current status and requester action """

    def __init__(self, status, expected, msg=''):
        """ Job current status is inconsistent for requested action
        :param status: current Job status
        :param expected: list oc expected status
        :param msg: extended message to add to standard exception message
        """
        message = u'[Inconsistent status: "%s"] - expected one of %s' % (status, [str(i[1]) for i in expected])
        if msg:
            message = '%s ' % msg + message
        super(JobInconsistentStateError, self).__init__(message)


class JobPrepareException(JobRunException):
    """Preparation process errors """
    pass
