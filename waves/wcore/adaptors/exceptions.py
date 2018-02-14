from __future__ import unicode_literals


class AdaptorException(Exception):
    """ Base adapter exception class, should be raise upon specific adapter class exception catch
    this exception class is supposed to be catched
    """
    pass


class AdaptorConnectException(AdaptorException):
    """
    adapter Connection Error
    """
    pass


class AdaptorExecException(AdaptorException):
    """
    adapter execution error
    """
    pass


class AdaptorNotAvailableException(AdaptorExecException):
    pass


class AdaptorJobException(AdaptorException):
    """
    adapter JobRun Exception
    """
    pass


class AdaptorNotReady(AdaptorException):
    """ adapter is not properly initialized to be used """
    pass


class AdaptorInitError(AdaptorException):
    """ Each adapter expects some attributes for initialization, this exception should be raised when some mandatory
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
