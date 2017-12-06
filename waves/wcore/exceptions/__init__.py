from __future__ import unicode_literals

import logging
import sys

__all__ = ['WavesException', 'RunnerException', 'RunnerNotInitialized', 'RunnerNotReady', 'RunnerConnectionError',
           'RunnerUnexpectedInitParam']

if sys.version_info[0] < 3:
    __all__ = [n.encode('utf-8') for n in __all__]

logger = logging.getLogger(__name__)


class WavesException(Exception):
    """
    Waves base exception class, exception log
    """

    def __init__(self, *args, **kwargs):
        super(WavesException, self).__init__(*args, **kwargs)
        logger.exception('[%s] - %s', self.__class__.__name__, self.message)


class RunnerException(WavesException):
    """
    Base Exception class for all Runner related errors
    """

    def __init__(self, *args, **kwargs):
        super(RunnerException, self).__init__(*args, **kwargs)


class RunnerNotInitialized(RunnerException):
    pass


class RunnerUnexpectedInitParam(RunnerException, KeyError):
    pass


class RunnerConnectionError(RunnerException):
    def __init__(self, reason, msg=''):
        message = reason
        if msg != '':
            message = '%s %s' % (msg, message)
        super(RunnerException, self).__init__(message)


class RunnerNotReady(RunnerException):
    pass
