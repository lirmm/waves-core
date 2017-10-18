from __future__ import unicode_literals

import os
import logging
import warnings
import datetime
import inflection
import re

from django.contrib.contenttypes.models import ContentType
from waves.wcore.adaptors.exceptions import *
from waves.wcore.models import Runner, get_service_model, get_submission_model
from waves.wcore.models.adaptors import AdaptorInitParam
from waves.wcore.utils.exception_logging_decorator import exception
from waves.wcore.settings import waves_settings

Service = get_service_model()
Submission = get_submission_model()

logger = logging.getLogger(__name__)


class AdaptorImporter(object):
    """Base AdaptorImporter class, define process which must be implemented in concrete sub-classes """
    _update = False
    _formatter = None
    _tool_client = None
    _order_input = 0
    _exit_codes = None
    #: Some fields on remote connectors need a mapping for type between standard WAVES and theirs
    _type_map = {}
    _warnings = []
    _errors = []

    def __init__(self, adaptor):
        """
        Initialize a Import from it's source adaptor
        :param adaptor: a JobAdaptor object, providing connection support
        """
        self.adaptor = adaptor
        self.service = None
        self.submission = None
        self._formatter = InputFormat()
        self._logger = logging.getLogger(logger.name)
        self._logger.propagate = False
        self._logger.setLevel(logging.INFO)

    def __str__(self):
        return self.__class__.__name__

    @property
    def connected(self):
        return self.adaptor.connected

    def log_file(self, tool_id):
        today = datetime.datetime.today().strftime('%Y%m%d_%H%M%S')
        return os.path.join(waves_settings.DATA_ROOT,
                            "%s_%s.log" % (today, inflection.underscore(re.sub(r'[^\w]+', '_', tool_id))))

    def load_tool_params(self, tool_id, for_submission):
        """ Load tool params : Inputs / Outputs / ExitCodes
        :return: None
        """
        raise NotImplementedError()

    def import_service(self, tool_id, for_service=None):
        """
        For specified Adaptor remote tool identifier, try to import submission params
        :param for_service: Specified is service should be updated or created
        :param tool_id: Adaptors provider remote tool identifier
        :return: Update service with new submission according to retrieved parameters
        :rtype: :class:`waves.wcore.adaptors.models.services.Service`
        """
        try:
            self.connect()
            self._warnings = []
            self._errors = []
            fh = logging.FileHandler(self.log_file(tool_id))
            formatter = logging.Formatter('[%(levelname)s] - %(message)s')
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
            # First load remote service details
            if for_service is None:
                self.service = self.load_tool_details(tool_id)
                # create from scratch a new one
                # Submission has been created from signal
                self.service.save()
                self.submission = self.service.default_submission
            else:
                # Update service values
                self.service = for_service
                self.service.status = Service.SRV_TEST
                self.submission = Submission(name="Imported from Galaxy",
                                             api_name="galaxy",
                                             service=self.service,
                                             availability=Submission.AVAILABLE_BOTH)
            self.submission.name = "Imported from Galaxy"
            self.submission.api_name = "galaxy"
            self.submission.save()
            self.service.save()

            self._logger.info('Import Service %s', tool_id)
            self._logger.info('Service %s', self.service.name)

            self.load_tool_params(tool_id, self.submission)
            # Add file handler
            self._logger.info('------------------------------------')
            self._logger.info(self.service)
            self._logger.info('------------------------------------')
            if self.warnings:
                self._logger.warn('*** // WARNINGS // ***')
                for warn in self.warnings:
                    self._logger.warn('=> %s', warn.message)
            if self.errors:
                self._logger.warn('*** // ERRORS // ***')
                for error in self.errors:
                    self._logger.error('=> %s', error.message)
            self._logger.info('------------')
            self._logger.info('-- Inputs --')
            self._logger.info('------------')
            for service_input in self.submission.inputs.all():
                self._logger.info("Name:%s;default:%s;required:%s", service_input, service_input.type,
                                   service_input.get_required_display())
                self._logger.debug("Full input:")
                [self._logger.debug('%s:%s', item, value) for (item, value) in vars(service_input).iteritems()]
            self._logger.info('-------------')
            self._logger.info('-- Outputs --')
            self._logger.info('-------------')
            for service_output in self.submission.outputs.all():
                self._logger.info(service_output)
                [self._logger.debug('%s:%s', item, value) for (item, value) in vars(service_output).iteritems()]
            self._logger.info('------------------------------------')
            self.adaptor.command = tool_id
            self.submission.save()
            return self.service, self.submission
        except ImporterException as e:
            return None, None

    def list_services(self):
        """ Get and return a list of tuple (['Service Objects' list])  """
        if not self.connected:
            self.connect()
        return self._list_services()

    def connect(self):
        return self.adaptor.connect()

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
        """
        Return a Service Object instance (not saved) with remote information
        :return: Service"""
        raise NotImplementedError()

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
