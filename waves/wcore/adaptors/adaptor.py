""" Base class for all JobRunnerAdaptor implementation, define main job workflow expected behaviour """
from __future__ import unicode_literals

import json
import logging

import waves.wcore.adaptors.const
from waves.wcore.adaptors.exceptions import AdaptorJobStateException
from waves.wcore.adaptors.utils import check_ready
from waves.wcore.utils.exception_logging_decorator import exception

logger = logging.getLogger(__name__)


class JobAdaptor(object):
    """
    Abstract JobAdaptor class, declare expected behaviour from any WAVES's JobAdaptor dependent ?
    """
    NOT_AVAILABLE_MESSAGE = "Adaptor is currently not available on platform"
    name = 'Abstract Adaptor name'
    #: Remote status need to be mapped with WAVES expected job status
    _states_map = {}

    def __init__(self, command='', protocol='http', host="localhost", **kwargs):
        """ Initialize a adaptor
        Set _initialized value (True or False) if all non default expected params are set
        :param kwargs: its possible to force connector and parser attributes when initialize a Adaptor
        :return: a new JobAdaptor object
        """
        self.command = command
        self.protocol = protocol
        self.host = host
        self.connector = kwargs.get('connector', None)
        self.parser = kwargs.get('parser', None)
        self._connected = False

    def init_value_editable(self, init_param):
        """ By default all fields are editable, override this function for your specific needs in your adaptor """
        return True

    @property
    def init_params(self):
        """ Returns expected (required) 'init_params', with default if set at class level
        :return: A dictionary containing expected init params
        :rtype: dict
        """
        return dict(command=self.command, protocol=self.protocol, host=self.host)

    @property
    def connected(self):
        """ Tells whether current remote adaptor object is connected to calculation infrastructure
        :return: True if actually connected / False either
        :rtype: bool
        """
        return self.connector is not None and self._connected is True

    @property
    def available(self):
        return True

    @exception(logger)
    def connect(self):
        """
        Connect to remote platform adaptor
        :raise: :class:`waves.wcore.adaptors.exceptions.adaptors.AdaptorConnectException`
        :return: connector reference or raise an
        """
        if not self.connected:
            self._connect()
        return self.connector

    @exception(logger)
    def disconnect(self):
        """ Shut down connection to adaptor. Called after job adaptor execution to disconnect from remote
        :raise: :class:`waves.wcore.adaptors.exceptions.adaptors.AdaptorConnectException`
        :return: Nothing
        """
        if self.connected:
            self._disconnect()
        self.connector = None
        self._connected = False

    @exception(logger)
    @check_ready
    def prepare_job(self, job):
        """ Job execution preparation process, may store prepared data in a pickled object
        :param job: The job to prepare execution for
        :raise: :class:`waves.wcore.adaptors.exceptions.RunnerNotReady` if adaptor is not initialized before call
        :raise: :class:`waves.wcore.adaptors.exceptions.JobPrepareException` if error during preparation process
        :raise: :class:`waves.wcore.adaptors.exceptions.JobInconsistentStateError` if job status is not 'created'
        """
        try:
            assert (job.status <= waves.wcore.adaptors.const.JOB_CREATED)
        except AssertionError:
            raise AdaptorJobStateException(job.status, waves.wcore.adaptors.const.JOB_CREATED)
        self.connect()
        self._prepare_job(job)
        job.status = waves.wcore.adaptors.const.JOB_PREPARED
        return job

    @exception(logger)
    @check_ready
    def run_job(self, job):
        """ Launch a previously 'prepared' job on the remote adaptor class
        :param job: The job to launch execution
        :raise: :class:`waves.wcore.adaptors.exceptions.RunnerNotReady` if adaptor is not initialized
        :raise: :class:`waves.wcore.adaptors.exceptions.JobRunException` if error during launch
        :raise: :class:`waves.wcore.adaptors.exceptions.JobInconsistentStateError` if job status is not 'prepared'
        """
        try:
            assert (job.status == waves.wcore.adaptors.const.JOB_PREPARED)
        except AssertionError:
            raise AdaptorJobStateException(job.status, waves.wcore.adaptors.const.JOB_PREPARED)
        self.connect()
        self._run_job(job)
        job.status = waves.wcore.adaptors.const.JOB_QUEUED
        return job

    @exception(logger)
    @check_ready
    def cancel_job(self, job):
        """ Cancel a running job on adaptor class, if possible
        :param job: The job to cancel
        :return: The new job status
        :rtype: int
        :raise: :class:`waves.wcore.adaptors.exceptions.JobRunException` if error during launch
        :raise: :class:`waves.wcore.adaptors.exceptions.JobInconsistentStateError` if job status is not 'prepared'
        """
        try:
            assert (job.status <= waves.wcore.adaptors.const.JOB_SUSPENDED)
        except AssertionError:
            raise AdaptorJobStateException(job.status, waves.wcore.adaptors.const.STATUS_MAP[0:5])
        self.connect()
        self._cancel_job(job)
        job.status = waves.wcore.adaptors.const.JOB_CANCELLED
        return job

    @exception(logger)
    @check_ready
    def job_status(self, job):
        """ Return current WAVES Job status
        :param job: current job
        :return: one of `waves.wcore.adaptors.STATUS_MAP`
        """
        self.connect()
        job.status = self._states_map[self._job_status(job)]
        logger.debug('Current remote state %s mapped to %s', self._job_status(job),
                     waves.wcore.adaptors.const.STATUS_MAP.get(job.status, 'Undefined'))
        return job

    @exception(logger)
    @check_ready
    def job_results(self, job):
        """ If job is done, return results
        :param job: current Job
        :return: a list a JobOutput
        """
        self.connect()
        self._job_results(job)
        return job

    @exception(logger)
    def job_run_details(self, job):
        """ Retrive job run details for job
        :param job: current Job
        :return: JobRunDetails object
        """
        self.connect()
        return self._job_run_details(job)

    def dump_config(self):
        """ Create string representation of current adaptor config"""
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
         :raise: `waves.wcore.adaptors.exception.AdaptorConnectException` if error
         :return: an instance of concrete connector implementation """
        raise NotImplementedError()

    def _disconnect(self):
        """ Actually disconnect from remote job runner platform
        :raise: `waves.wcore.adaptors.exception.AdaptorConnectException` if error """
        raise NotImplementedError()

    def _prepare_job(self, job):
        """ Actually do preparation for job if needed by concrete adaptor.
        For example:
            - prepare and upload input files to remote host
            - set up parameters according to concrete adaptor needs
        :raise: `waves.wcore.adaptors.exception.AdaptorException` if error """
        raise NotImplementedError()

    def _run_job(self, job):
        """ Actually launch job on concrete adaptor
        :raise: `waves.wcore.adaptors.exception.AdaptorException` if error """
        raise NotImplementedError()

    def _cancel_job(self, job):
        """ Try to cancel job on concrete adaptor
        :raise: `waves.wcore.adaptors.exception.AdaptorException` if error """
        raise NotImplementedError()

    def _job_status(self, job):
        """ Actually retrieve job states on concrete adaptor, return raw value to be mapped with defined in _states_map
        :raise: `waves.wcore.adaptors.exception.AdaptorException` if error """
        raise NotImplementedError()

    def _job_results(self, job):
        """ Retrieve job results from concrete adaptor, may include some file download from remote hosts
        Set attribute result_available for job if success
        :raise: `waves.wcore.adaptors.exception.AdaptorException` if error
        :return: Boolean True if results are retrieved from remote host, False either
        """
        raise NotImplementedError()

    def _job_run_details(self, job):
        """ Retrieve job run details if possible from concrete adaptor
        :raise: `waves.wcore.adaptors.exception.AdaptorException` if error """
        return job.default_run_details()

    def _dump_config(self):
        """ Return string representation of concrete adaptor configuration
        :return: a String representing configuration """
        return str([(item, value) for (item, value) in vars(self).iteritems()])

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
            "clazz": ".".join([self.__module__, self.__class__.__name__]),
            "params": self.init_params
        })
