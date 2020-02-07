

import logging
import os
import stat

from django.conf import settings

logger_file = logging.getLogger(__name__)


class LoggerClass(object):
    LOG_LEVEL = logging.DEBUG
    log_dir = os.path.dirname(settings.BASE_DIR)
    _logger = None

    @property
    def logger(self):
        """ Get or create a new logger for this job

        :return: Logger"""
        self._logger = logging.getLogger(self.logger_name)
        if not len(self._logger.handlers):
            # Add handler only once !
            try:
                hdlr = logging.FileHandler(self.log_file)
                mode = os.stat(self.log_file).st_mode
                if not bool(mode & stat.S_IWGRP):
                    os.chmod(self.log_file, 0o664)
                formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
                hdlr.setFormatter(formatter)
                self._logger.propagate = False
                self._logger.addHandler(hdlr)
                self._logger.setLevel(self.LOG_LEVEL)
            except IOError as err:
                self._logger = logging.getLogger("waves.errors")
                self._logger.warning('This object %s is not able to log where it should %s', self.pk, self.log_file)
                logger_file.exception("IO Error in %s: %s", self.__class__.__name__, err.message)
        return self._logger

    @property
    def log_file(self):
        """ Return path to job dedicated log file

        :return: str"""
        return os.path.join(self.log_dir, self.logger_file_name)

    @property
    def logger_name(self):
        return self.__class__.__name__

    @property
    def logger_file_name(self):
        return self.logger_name + '.log'
