"""
Adaptor specific exceptions
"""
from __future__ import unicode_literals

import waves.adaptors.core

__all__ = ['AdaptorException',
           'AdaptorConnectException',
           'AdaptorExecException',
           'AdaptorJobException',
           'AdaptorInitError',
           'AdaptorNotReady',
           'AdaptorJobStateException']


class AdaptorException(Exception):
    """ Base Adaptor exception class, should be raise upon specific Adaptor class exception catch
    this exception class is supposed to be catched
    """

    def __init__(self, msg, parent=None):
        if parent is not None:
            # Retrieve parent exception message in case
            self._parent = parent
            self._full_msg = '{0} - [from:{1}] {2}'.format(msg.decode('utf-8'), parent.__class__.__name__,
                                                           parent.message.decode('utf-8', errors='replace'))
        else:
            self._full_msg = msg
        Exception.__init__(self, msg)

    def get_full_message(self):
        return self._full_msg

    full_message = property(get_full_message)


class AdaptorConnectException(AdaptorException):
    """
    Adaptor Connection Error
    """
    pass


class AdaptorExecException(AdaptorException):
    """
    Adaptor execution error
    """
    pass


class AdaptorJobException(AdaptorException):
    """
    Adaptor JobRun Exception
    """
    pass


class AdaptorJobStateException(AdaptorJobException):
    def __init__(self, status, expected, parent=None):
        if expected is not list:
            expected = [expected]
        msg = "Wrong job state, excepted %s, got %s" % ([waves.adaptors.core.STATUS_MAP[state] for state in expected],
                                                        waves.adaptors.core.STATUS_MAP[status])
        super(AdaptorJobStateException, self).__init__(msg, parent=parent)


class AdaptorNotReady(Exception):
    """ Adaptor is not properly initialized to be used """

    def __init__(self):
        super(AdaptorNotReady, self).__init__('Adaptor is not ready')


class AdaptorInitError(AttributeError):
    """ Each adaptor expects some attributes for initialization, this exception should be raised when some mandatory
    parameters are missing
    """
    pass
