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
import logging
import re
import warnings

import inflection

from waves.core.exceptions import ImporterException
from waves.models import Submission
from waves.settings import waves_settings
from waves.core.utils import LoggerClass

logger = logging.getLogger(__name__)


class AdaptorImporter(LoggerClass):
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

    LOG_LEVEL = waves_settings.JOB_LOG_LEVEL

    @property
    def log_dir(self):
        return waves_settings.DATA_ROOT

    @property
    def logger_name(self):
        return 'waves.importer.%s' % str(self.tool_id)

    @property
    def logger_file_name(self):
        return "%s_%s.log" % (
            self.adaptor, inflection.underscore(re.sub(r'[^\w]+', '_', self.tool_id)))

    def __init__(self, adaptor):
        """
        Initialize a Import from it's source adapter

        :param adaptor: a JobAdaptor object, providing connection support
        """
        self.adaptor = adaptor
        self.service = None
        self.submission = None
        self._formatter = InputFormat()
        self.tool_id = adaptor.name

    def __str__(self):
        return self.__class__.__name__

    def __unicode__(self):
        return self.__class__.__name__

    @property
    def connected(self):
        return self.adaptor.connected

    def load_tool_params(self, tool_id, for_submission):
        """ Load tool params : Inputs / Outputs / ExitCodes
        :return: None
        """
        raise NotImplementedError()

    def import_service(self, tool_id, for_service=None, update_service=False):
        """
        For specified adapter remote tool identifier, try to import submission params

        :param update_service: update or not for_service if specified
        :param for_service: Specified is service should be updated or created
        :param tool_id: adapters provider remote tool identifier
        :return: Update service with new submission according to retrieved parameters
        :rtype: :class:`waves.core.mocks.models.services.Service`
        """
        try:
            self.tool_id = tool_id
            self.connect()
            self._warnings = []
            self._errors = []
            # setup dedicated log file
            tool_detailed_info = self.load_tool_details(tool_id)
            log_file = self.log_file
            fh = logging.FileHandler(log_file, 'w+')
            formatter = logging.Formatter('[%(asctime)s][%(levelname)s]: %(message)s')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
            # First load remote service details
            self.logger.info('------------------------------------')
            self.logger.info('Import remote service: %s', tool_id)
            if for_service is None:
                self.service = tool_detailed_info
                self.logger.info('=> to new service: %s', self.service.name)
                # create from scratch a new one
                # Submission has been created from signal
                self.service.adaptor = self.adaptor
                self.service.save()

                self.submission = self.service.default_submission
                self.submission.name = "Imported from Galaxy"
                self.submission.availability = Submission.NOT_AVAILABLE
                self.submission.save()
            else:
                # Update service values
                self.service = for_service
                self.logger.info('=> to existing service: %s', self.service.name)
                if update_service:
                    self.logger.info('Updating service data from remote...')
                    self.service.version = tool_detailed_info.version
                    # save new updates
                    self.service.save()
                self.submission = Submission.objects.create(name="Imported from Galaxy",
                                                            api_name="galaxy",
                                                            service=self.service,
                                                            availability=Submission.NOT_AVAILABLE)
                self.logger.info("=> created new submission %s/%s", self.submission.name, self.submission.api_name)
            self.logger.debug('----------- IMPORT PARAMS --------------')
            self.load_tool_params(tool_id, self.submission)
            self.logger.debug('----------- //IMPORT PARAMS ------------')
            self.logger.info('------------- IMPORT REPORT ----------')
            if self.warnings:
                self.logger.warning('*** // WARNINGS // ***')
                for warn in self.warnings:
                    self.logger.warning('=> %s', warn.message)
            if self.errors:
                self.logger.warning('*** // ERRORS // ***')
                for error in self.errors:
                    self.logger.error('=> %s', error.message)
            self.logger.info('------------')
            self.logger.info('-- Inputs --')
            self.logger.info('------------')
            for service_input in self.submission.inputs.all():
                self.logger.info("Name:%s;default:%s;required:%s", service_input, service_input.type,
                                 service_input.get_required_display())
                self.logger.debug("Full input:")
                [self.logger.debug('%s: %s', item, value) for (item, value) in vars(service_input).items()]
            self.logger.info('-------------')
            self.logger.info('-- Outputs --')
            self.logger.info('-------------')
            for service_output in self.submission.outputs.all():
                self.logger.info(service_output)
                [self.logger.debug('%s: %s', item, value) for (item, value) in vars(service_output).items()]
            self.logger.info('------------------------------------')
            self.adaptor.command = tool_id
            self.submission.save()
            return self.service, self.submission
        except ImporterException as e:
            logger.exception("Import service error %s", e)
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
        """ Map remote adapter types to JobInput/JobOutput WAVES TYPE"""
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
                warnings.warn('Error Parsing list values %s - value:%s - param:%s', e, value, param)
        return list_choice
