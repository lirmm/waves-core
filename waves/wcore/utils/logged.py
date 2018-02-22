from __future__ import unicode_literals

import logging
import os
from django.conf import settings
import stat


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
            hdlr = logging.FileHandler(self.log_file)
            try:
                mode = os.stat(self.log_file).st_mode
                if not bool(mode & stat.S_IWGRP):
                    os.chmod(self.log_file, 0o664)
            except OSError as e:
                logger = logging.getLogger()
                logger.exception("Hard exception %s %s", e.message, e.filename)
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            hdlr.setFormatter(formatter)
            self._logger.propagate = False
            self._logger.addHandler(hdlr)
            self._logger.setLevel(self.LOG_LEVEL)
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
