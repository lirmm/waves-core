import logging
import sys

__all__ = ['WavesException', 'RunnerException', 'RunnerNotInitialized', 'RunnerNotReady', 'RunnerConnectionError',
           'RunnerUnexpectedInitParam']

if sys.version_info[0] < 3:
    __all__ = [n.encode('utf-8') for n in __all__]

logger = logging.getLogger(__name__)


class WavesException(Exception):
    """
    Waves base exception class, simply log exception in standard web logs
    TODO: This class may be obsolete depending of running / logging configuration
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        logger.exception('[%s] - %s', self.__class__.__name__, self)


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
