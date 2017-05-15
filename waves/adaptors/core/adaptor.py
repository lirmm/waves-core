""" Base class for all JobRunnerAdaptor implementation, define main job workflow expected behaviour """
from __future__ import unicode_literals

import abc
import waves.adaptors.core
from waves.adaptors.exceptions.adaptors import AdaptorInitError, AdaptorNotReady, AdaptorJobStateException
import logging
import warnings

logger = logging.getLogger(__name__)


class JobAdaptor(object):
    """
    Abstract JobAdaptor class, declare expected behaviour from any WAVES's JobAdaptor dependent ?
    """
    __metaclass__ = abc.ABCMeta

    NOT_AVAILABLE_MESSAGE = "Adaptor is currently not available on platform"

    name = 'Abstract Adaptor name'
    #: Remote command for Job execution
    command = None
    #: Defined remote connector, depending on subclass implementation
    connector = None
    #: Some connector need to parse requested job in order to create a remote job
    parser = None

    protocol = 'http'
    protocol_default = 'http'

    #: Host
    host = 'localhost'
    #: Remote status need to be mapped with WAVES expected job status
    _states_map = {}
    _init_params = {}

    def __init__(self, *args, **kwargs):
        """ Initialize a adaptor
        Set _initialized value (True or False) if all non default expected params are set
        :raise: :class:`waves.adaptors.exceptions.adaptors.AdaptorInitError` if wrong parameter given as init values
        :param init_params: a dictionnary with expected initialization params (retrieved from init_params property)
        :param kwargs: its possible to force connector and _parser attributes when initialize a Adaptor
        :return: a new JobAdaptor object
        """
        self._initialized = False
        self._connected = False
        self.connector = kwargs['connector'] if 'connector' in kwargs else None
        self.parser = kwargs['parser'] if 'parser' in kwargs else None
        if 'init_params' in kwargs and kwargs['init_params'] is not None:
            try:
                for name, value in kwargs['init_params'].items():
                    getattr(self, name)
                    setattr(self, name, value)
            except AttributeError as e:
                raise AdaptorInitError(e.message)
        self._initialized = all(init_param is not None for init_param in self.init_params)

    def __str__(self):
        return '.'.join([self.__class__.__module__, self.__class__.__name__])

    def init_value_editable(self, init_param):
        return True

    @property
    def name(self):
        """ Return Adaptor displayed name """
        return self.name

    @property
    def init_params(self):
        """ Returns expected 'init_params', with default if set at class level
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

    def connect(self):
        """
        Connect to remote platform adaptor
        :raise: :class:`waves.adaptors.exceptions.adaptors.AdaptorConnectException`
        :return: connector reference or raise an
        """
        if not self._initialized:
            raise AdaptorNotReady()
        if not self.connected:
            self._connect()
        return self.connector

    def disconnect(self):
        """ Shut down connection to adaptor. Called after job adaptor execution to disconnect from remote
        :raise: :class:`waves.adaptors.exceptions.adaptors.AdaptorConnectException`
        :return: Nothing
        """
        if self.connected:
            self._disconnect()
        self.connector = None
        self._connected = False

    def prepare_job(self, job):
        """ Job execution preparation process, may store prepared data in a pickled object
        :param job: The job to prepare execution for
        :raise: :class:`waves.adaptors.exceptions.RunnerNotReady` if adaptor is not initialized before call
        :raise: :class:`waves.adaptors.exceptions.JobPrepareException` if error during preparation process
        :raise: :class:`waves.adaptors.exceptions.JobInconsistentStateError` if job status is not 'created'
        """
        try:
            assert (job.status <= waves.adaptors.core.JOB_CREATED)
        except AssertionError:
            raise AdaptorJobStateException(job.status, waves.adaptors.core.JOB_CREATED)
        self.connect()
        self._prepare_job(job)
        job.status = waves.adaptors.core.JOB_PREPARED
        return job

    def run_job(self, job):
        """ Launch a previously 'prepared' job on the remote adaptor class
        :param job: The job to launch execution
        :raise: :class:`waves.adaptors.exceptions.RunnerNotReady` if adaptor is not initialized
        :raise: :class:`waves.adaptors.exceptions.JobRunException` if error during launch
        :raise: :class:`waves.adaptors.exceptions.JobInconsistentStateError` if job status is not 'prepared'
        """
        try:
            assert (job.status == waves.adaptors.core.JOB_PREPARED)
        except AssertionError:
            raise AdaptorJobStateException(job.status, waves.adaptors.core.JOB_PREPARED)
        self.connect()
        self._run_job(job)
        job.status = waves.adaptors.core.JOB_QUEUED
        return job

    def cancel_job(self, job):
        """ Cancel a running job on adaptor class, if possible
        :param job: The job to cancel
        :return: The new job status
        :rtype: int
        :raise: :class:`waves.adaptors.exceptions.JobRunException` if error during launch
        :raise: :class:`waves.adaptors.exceptions.JobInconsistentStateError` if job status is not 'prepared'
        """
        try:
            assert (job.status <= waves.adaptors.core.JOB_SUSPENDED)
        except AssertionError:
            raise AdaptorJobStateException(job.status, waves.adaptors.core.STATUS_MAP[0:5])
        self.connect()
        self._cancel_job(job)
        job.status = waves.adaptors.core.JOB_CANCELLED
        return job

    def job_status(self, job):
        """ Return current WAVES Job status
        :param job: current job
        :return: one of `waves.adaptors.STATUS_MAP`
        """
        self.connect()
        status = self._states_map[self._job_status(job)]
        logger.debug('Current remote state %s mapped to %s', self._job_status(job),
                     waves.adaptors.core.STATUS_MAP.get(status, 'Undefined'))
        job.status = status
        return job

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
        details = self._job_run_details(job)
        return details

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

    @abc.abstractmethod
    def _connect(self):
        """ Actually do connect to concrete remote job runner platform,
         :raise: `waves.adaptors.exception.AdaptorConnectException` if error
         :return: an instance of concrete connector implementation """
        raise NotImplementedError()

    @abc.abstractmethod
    def _disconnect(self):
        """ Actually disconnect from remote job runner platform
        :raise: `waves.adaptors.exception.AdaptorConnectException` if error """
        raise NotImplementedError()

    @abc.abstractmethod
    def _prepare_job(self, job):
        """ Actually do preparation for job if needed by concrete adaptor.
        For example:
            - prepare and upload input files to remote host
            - set up parameters according to concrete adaptor needs
        :raise: `waves.adaptors.exception.AdaptorException` if error """
        raise NotImplementedError()

    @abc.abstractmethod
    def _run_job(self, job):
        """ Actually launch job on concrete adaptor
        :raise: `waves.adaptors.exception.AdaptorException` if error """
        raise NotImplementedError()

    @abc.abstractmethod
    def _cancel_job(self, job):
        """ Try to cancel job on concrete adaptor
        :raise: `waves.adaptors.exception.AdaptorException` if error """
        raise NotImplementedError()

    @abc.abstractmethod
    def _job_status(self, job):
        """ Actually retrieve job states on concrete adaptor, return raw value to be mapped with defined in _states_map
        :raise: `waves.adaptors.exception.AdaptorException` if error """
        raise NotImplementedError()

    @abc.abstractmethod
    def _job_results(self, job):
        """ Retrieve job results from concrete adaptor, may include some file download from remote hosts
        Set attribute result_available for job if success
        :raise: `waves.adaptors.exception.AdaptorException` if error
        :return: Boolean True if results are retrieved from remote host, False either
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _job_run_details(self, job):
        """ Retrieve job run details if possible from concrete adaptor
        :raise: `waves.adaptors.exception.AdaptorException` if error """
        raise NotImplementedError()

    def _dump_config(self):
        """ Return string representation of concrete adaptor configuration
        :return: a String representing configuration """
        return ""

    def test_connection(self):
        self.connect()
        return self.connected

    def connexion_string(self):
        return "%s://%s" % (self.protocol, self.host)

    @property
    def importer(self):
        return None


class AdaptorImporter(object):
    """Base AdaptorImporter class, define process which must be implemented in concrete sub-classes """
    __metaclass__ = abc.ABCMeta
    _update = False
    _service = None
    _runner = None
    _formatter = None
    _tool_client = None
    _order_input = 0
    _submission = None
    _exit_codes = None
    #: Some fields on remote connectors need a mapping for type between standard WAVES and theirs
    _type_map = {}
    _warnings = []
    _errors = []

    def __init__(self, adaptor, formatter=None):
        """
        Initialize a Import from it's source adaptor
        :param adaptor: a JobAdaptor object, providing connection support
        """
        self._formatter = InputFormat() if formatter is None else formatter
        self._adaptor = adaptor

    def __str__(self):
        return self.__class__.__name__

    @property
    def connected(self):
        return self._adaptor.connected

    def import_service(self, tool_id):
        """
        For specified Adaptor remote tool identifier, try to import submission params
        :param tool_id: Adaptors provider remote tool identifier
        :return: Update service with new submission according to retrieved parameters
        :rtype: :class:`waves.adaptors.models.services.Service`
        """
        self.connect()
        self._warnings = []
        self._errors = []
        service_details, inputs, outputs, exit_codes = self.load_tool_details(tool_id)
        if service_details:
            logger.debug('Import Service %s', tool_id)
            self._service = service_details
            logger.debug('Service %s', service_details.name)
            self._service.inputs = self.import_service_params(inputs)
            self._service.outputs = self.import_service_outputs(outputs)
            self._service.exit_codes = self.import_exit_codes(exit_codes)
        else:
            logger.warn('No service retrieved (%s)', tool_id)
            return None
        # TODO manage exit codes
        logger_import = logging.getLogger('import_tool_logger')
        logger_import.setLevel(logging.INFO)
        logger_import.info('------------------------------------')
        logger_import.info(self._service.info())
        logger_import.info('------------------------------------')
        if self.warnings or self.errors:
            logger_import.warn('*** // WARNINGS // ***')
            for warn in self.warnings:
                logger_import.warn('=> %s', warn.message)
        if self.errors:
            logger_import.warn('*** // ERRORS // ***')
            for error in self.errors:
                logger_import.error('=> %s', error.message)
        logger_import.info('------------')
        logger_import.info('-- Inputs --')
        logger_import.info('------------')
        for service_input in self._service.inputs:
            logger_import.info(service_input.info())
        logger_import.info('-------------')
        logger_import.info('-- Outputs --')
        logger_import.info('-------------')
        for service_output in self._service.outputs:
            logger_import.info(service_output.info())
        logger_import.info('------------------------------------')
        return self._service

    def list_services(self):
        """ Get and return a list of tuple ('Category, ['Service Objects' list])  """
        if not self.connected:
            self.connect()
        return self._list_services()

    def connect(self):
        return self._adaptor.connect()

    @property
    def warnings(self):
        return self._warnings

    def warn(self, base_warn):
        self._warnings.append(base_warn)

    @property
    def errors(self):
        return self._errors

    def error(self, base_error):
        if base_error is None:
            return self._errors
        self._errors.append(base_error)

    @abc.abstractmethod
    def import_service_params(self, data):
        raise NotImplementedError()

    @abc.abstractmethod
    def import_service_outputs(self, data):
        raise NotImplementedError()

    @abc.abstractmethod
    def import_exit_codes(self, tool_id):
        raise NotImplementedError()

    @abc.abstractmethod
    def load_tool_details(self, tool_id):
        """ Return a Service Object instance with added information if possible """
        return NotImplementedError()

    @abc.abstractmethod
    def _list_services(self):
        raise NotImplementedError()

    def map_type(self, type_value):
        """ Map remote adaptor types to JobInput/JobOutput WAVES TYPE"""
        return self._type_map.get(type_value, 'text')


class InputFormat(object):
    """
    ServiceInput format validation
    """

    @staticmethod
    def format_number(number):
        return number

    @staticmethod
    def format_boolean(truevalue, falsevalue):
        return '{}|{}'.format(truevalue, falsevalue)

    @staticmethod
    def format_interval(minimum, maximum):
        return '{}|{}'.format(minimum, maximum)

    @staticmethod
    def format_list(values):
        import os
        return os.linesep.join([x.strip(' ') for x in values])

    @staticmethod
    def choice_list(value):
        list_choice = []
        param = ''
        if value:
            try:
                for param in value.splitlines(False):
                    if '|' in param:
                        val = param.split('|')
                        list_choice.append((val[1], val[0]))
                    else:
                        list_choice.append((param, param))
            except ValueError as e:
                warnings.warn('Error Parsing list values %s - value:%s - param:%s', e.message, value, param)
        return list_choice
