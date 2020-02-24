"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the GNU GPL v3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       https://www.gnu.org/licenses/gpl-3.0.en.html
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
from waves.core.exceptions.base import WavesException

__all__ = ['JobException', 'JobRunException', 'JobSubmissionException', 'JobCreateException',
           'JobMissingMandatoryParam', 'JobInconsistentStateError']


class JobException(WavesException):
    """ Base Exception class for all job related errors  """

    def __init__(self, message, job=None):
        if job:
            message = '[job:%s][%s] - %s' % (job.slug, job.remote_job_id, message)
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


class JobInconsistentStateError(JobException):
    """ Job current status is inconsistent for requested action

    """

    def __init__(self, message="", job=None, expected=None):
        """
        :param job: current Job
        :param expected: list oc expected status
        :param message: extended message to add to standard log_exception message
        """
        if expected is None:
            expected = []
        if job:
            message = u'{} [{}] - Inconsistent job  state: "{}" - expected {}'.format(
                message, job.slug, job.get_status_display(), [str(i[1]) for i in expected], )
        super(JobInconsistentStateError, self).__init__(message)
