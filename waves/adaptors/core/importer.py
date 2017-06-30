import logging
import warnings

from waves.adaptors.exceptions import *
from waves.utils.exception_logging_decorator import exception

logger = logging.getLogger(__name__)


class AdaptorImporter(object):
    """Base AdaptorImporter class, define process which must be implemented in concrete sub-classes """
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

    @exception(logger)
    def import_service(self, tool_id):
        """
        For specified Adaptor remote tool identifier, try to import submission params
        :param tool_id: Adaptors provider remote tool identifier
        :return: Update service with new submission according to retrieved parameters
        :rtype: :class:`waves.adaptors.models.services.Service`
        """
        try:
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
        except ImporterException as e:

            return None

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

    def import_service_params(self, data):
        raise NotImplementedError()

    def import_service_outputs(self, data):
        raise NotImplementedError()

    def import_exit_codes(self, tool_id):
        raise NotImplementedError()

    def load_tool_details(self, tool_id):
        """ Return a Service Object instance with added information if possible """
        return NotImplementedError()

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