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
import json

from waves.core.adaptors.utils import check_ready
from waves.core.const import JobStatus
from waves.core.exceptions import AdaptorException, JobInconsistentStateError


class JobAdaptor:
    """
    Abstract Jobadapter class, declare expected behaviour from any WAVES's Jobadapter dependent ?
    """
    _required = {'command', 'protocol', 'host'}

    NOT_AVAILABLE_MESSAGE = "adapter is currently not available on platform"
    name = 'Abstract adapter'
    #: Remote status need to be mapped with WAVES expected job status
    _states_map = {}

    def __str__(self):
        return self.__class__.__name__

    def __init__(self, command='', protocol='', host="localhost", **kwargs):
        """ Initialize a adapter
        Set _initialized value (True or False) if all non default expected params are set

        :param kwargs: its possible to force connector and parser attributes when initialize a adapter
        :return: a new Jobadapter object
        """
        self.command = command
        self.protocol = protocol
        self.host = host
        self.connector = kwargs.get(str('connector'), None)
        self.parser = kwargs.get(str('parser'), None)
        self._connected = False

    def init_value_editable(self, init_param):
        """ By default all fields are editable, override this function for your specific needs in your adapter """
        return True


    @property
    def init_params(self):
        """
        Returns expected (required) 'init_params', with default if set at class level

        :return: A dictionary containing expected init params
        :rtype: dict
        """
        return dict(command=self.command, protocol=self.protocol, host=self.host)

    @property
    def connected(self):
        """ Tells whether current remote adapter object is connected to calculation infrastructure

        :return: True if actually connected / False either
        :rtype: bool
        """
        return self.connector is not None and self._connected is True

    @property
    def available(self):
        # True by default
        return True

    def connect(self):
        """
        Connect to remote platform adapter

        :raise: :class:`waves.core.mocks.exceptions.mocks.AdaptorConnectException`
        :return: connector reference or raise an
        """
        if not self.connected:
            self._connect()
        return self.connector

    def disconnect(self):
        """ Shut down connection to adapter. Called after job adapter execution to disconnect from remote

        :raise: :class:`waves.core.mocks.exceptions.mocks.AdaptorConnectException`
        :return: Nothing
        """
        if self.connected:
            self._disconnect()
        self.connector = None
        self._connected = False

    @check_ready
    def prepare_job(self, job):
        """ Job execution preparation process, may store prepared data in a pickled object

        :param job: The job to prepare execution for
        :raise: :class:`waves.core.mocks.exceptions.RunnerNotReady` if adaptor is not initialized before call
        :raise: :class:`waves.core.mocks.exceptions.JobPrepareException` if error during preparation process
        :raise: :class:`waves.core.mocks.exceptions.JobInconsistentStateError` if job status is not 'created'
        """
        if job.status > JobStatus.JOB_CREATED:
            raise JobInconsistentStateError(job=job, expected=[JobStatus.STATUS_LIST[1]])
        self.connect()
        self._prepare_job(job)
        job.status = JobStatus.JOB_PREPARED
        return job

    @check_ready
    def run_job(self, job):
        """ Launch a previously 'prepared' job on the remote adapter class

        :param job: The job to launch execution
        :raise: :class:`waves.core.mocks.exceptions.RunnerNotReady` if adapter is not initialized
        :raise: :class:`waves.core.mocks.exceptions.JobRunException` if error during launch
        :raise: :class:`waves.core.mocks.exceptions.JobInconsistentStateError` if job status is not 'prepared'
        """
        if job.status != JobStatus.JOB_PREPARED:
            raise JobInconsistentStateError(job=job, expected=[JobStatus.STATUS_LIST[2]])
        self.connect()
        self._run_job(job)
        job.status = JobStatus.JOB_QUEUED
        return job

    @check_ready
    def cancel_job(self, job):
        """ Cancel a running job on adapter class, if possible

        :param job: The job to cancel
        :return: The new job status
        :rtype: int
        :raise: :class:`waves.core.mocks.exceptions.JobRunException` if error during launch
        :raise: :class:`waves.core.mocks.exceptions.JobInconsistentStateError` if job status is not 'prepared'
        """
        if job.status >= JobStatus.JOB_COMPLETED:
            raise JobInconsistentStateError(job=job, expected=JobStatus.STATUS_LIST[0:5],
                                            message="Job can't be cancelled")
        self.connect()
        try:
            self._cancel_job(job)
            job.status = JobStatus.JOB_CANCELLED
        except AdaptorException as exc:
            job.job_history.create(
                message="Job for %s '%s' could not be remotely cancelled: %s " % (self.__class__.__name__,
                                                                                  job.remote_job_id,
                                                                                  exc),
                status=job.status,
                is_admin=True)
        return job

    @check_ready
    def job_status(self, job):
        """ Return current WAVES Job status

        :param job: current job
        :return: one of `waves.core.mocks.STATUS_MAP`
        """
        self.connect()
        job.status = self._states_map[self._job_status(job)]
        job.logger.info('Current remote state %s mapped to %s', self._job_status(job),
                        JobStatus.STATUS_MAP.get(job.status, 'Undefined'))
        return job

    @check_ready
    def job_results(self, job):
        """ If job is done, return results

        :param job: current Job
        :return: a list a JobOutput
        """
        self.connect()
        self._job_results(job)
        return job

    def job_run_details(self, job):
        """ Retrive job run details for job

        :param job: current Job
        :return: JobRunDetails object
        """
        self.connect()
        return self._job_run_details(job)

    def dump_config(self):
        """ Create string representation of current adapter config"""
        str_dump = 'Dump config for %s \n ' % self.__class__
        str_dump += 'Init params:'
        for key, param in self.init_params.items():
            if key.startswith('crypt'):
                value = "*" * len(param)
            else:
                value = getattr(self, key)
            str_dump += ' - %s : %s ' % (key, value)
        extra_dump = self._dump_config()
        return str_dump + extra_dump

    def _connect(self):
        """ Actually do connect to concrete remote job runner platform,

         :raise: `waves.core.mocks.exception.AdaptorConnectException` if error
         :return: an instance of concrete connector implementation """
        raise NotImplementedError()

    def _disconnect(self):
        """ Actually disconnect from remote job runner platform

        :raise: `waves.core.mocks.exception.AdaptorConnectException` if error """
        raise NotImplementedError()

    def _prepare_job(self, job):
        """ Actually do preparation for job if needed by concrete adapter.
        For example:
            - prepare and upload input files to remote host
            - set up parameters according to concrete adapter needs

        :raise: `waves.core.mocks.exception.AdaptorException` if error """
        raise NotImplementedError()

    def _run_job(self, job):
        """ Actually launch job on concrete adapter

        :raise: `waves.core.mocks.exception.AdaptorException` if error """
        raise NotImplementedError()

    def _cancel_job(self, job):
        """ Try to cancel job on concrete adapter

        :raise: `waves.core.mocks.exception.AdaptorException` if error """
        raise NotImplementedError()

    def _job_status(self, job):
        """ Actually retrieve job states on concrete adapter, return raw value to be mapped with defined in _states_map

        :raise: `waves.core.mocks.exception.AdaptorException` if error """
        raise NotImplementedError()

    def _job_results(self, job):
        """ Retrieve job results from concrete adapter, may include some file download from remote hosts
        Set attribute result_available for job if success

        :raise: `waves.core.mocks.exception.AdaptorException` if error
        :return: Boolean True if results are retrieved from remote host, False either
        """
        raise NotImplementedError()

    def _job_run_details(self, job):
        """ Retrieve job run details if possible from concrete adapter

        :raise: `waves.core.mocks.exception.AdaptorException` if error """
        return job.default_run_details()

    def _dump_config(self):
        """ Return string representation of concrete adapter configuration

        :return: a String representing configuration """
        return str([(item, value) for (item, value) in vars(self).items()])

    def test_connection(self):
        self.connect()
        return self.connected

    def connexion_string(self):
        return "%s://%s" % (self.protocol, self.host)

    @property
    def importer(self):
        return None

    def serialize(self):
        return json.dumps({
            "clazz": self.class_name,
            "params": self.init_params
        })

    @property
    def class_name(self):
        return "{}.{}".format(self.__module__, self.__class__.__name__)
