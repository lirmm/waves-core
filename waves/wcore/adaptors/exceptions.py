from __future__ import unicode_literals

import waves.wcore.adaptors.const


class AdaptorException(Exception):
    """ Base Adaptor exception class, should be raise upon specific Adaptor class exception catch
    this exception class is supposed to be catched
    """
    pass


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


class AdaptorNotAvailableException(AdaptorExecException):
    pass


class AdaptorJobException(AdaptorException):
    """
    Adaptor JobRun Exception
    """
    pass


class AdaptorNotReady(AdaptorException):
    """ Adaptor is not properly initialized to be used """
    pass


class AdaptorInitError(AdaptorException):
    """ Each adaptor expects some attributes for initialization, this exception should be raised when some mandatory
    parameters are missing
    """
    pass


class ImporterException(AdaptorException):
    pass


class UnmanagedException(ImporterException):
    base_msg = ''

    def __init__(self, *args, **kwargs):
        super(UnmanagedException, self).__init__(*args, **kwargs)
        self.message = self.base_msg + self.message


class UnManagedAttributeException(UnmanagedException):
    base_msg = "Unmanaged Attribute: "

    def __init__(self, *args, **kwargs):
        super(UnManagedAttributeException, self).__init__(*args, **kwargs)


class UnManagedAttributeTypeException(UnmanagedException):
    base_msg = "Unmanaged Type: "

    def __init__(self, *args, **kwargs):
        super(UnManagedAttributeTypeException, self).__init__(*args, **kwargs)


class UnmanagedInputTypeException(UnmanagedException):
    base_msg = "Unmanaged Input: "

    def __init__(self, *args, **kwargs):
        super(UnmanagedInputTypeException, self).__init__(*args, **kwargs)
