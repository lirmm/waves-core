import waves.core.adaptors


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


class AdaptorNotAvailableException(AdaptorExecException):
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
        msg = "Wrong job state, excepted %s, got %s" % ([waves.core.adaptors.const.STATUS_MAP[state] for state in expected],
                                                        waves.core.adaptors.const.STATUS_MAP[status])
        super(AdaptorJobStateException, self).__init__(msg, parent=parent)


class AdaptorNotReady(Exception):
    """ Adaptor is not properly initialized to be used """
    pass


class AdaptorInitError(AttributeError):
    """ Each adaptor expects some attributes for initialization, this exception should be raised when some mandatory
    parameters are missing
    """
    pass


class ImporterException(BaseException):
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
    base_msg = "Unmanaged Attribute type: "

    def __init__(self, *args, **kwargs):
        super(UnManagedAttributeTypeException, self).__init__(*args, **kwargs)


class UnmanagedInputTypeException(UnmanagedException):
    base_msg = "Unmanaged Input type: "

    def __init__(self, *args, **kwargs):
        super(UnmanagedInputTypeException, self).__init__(*args, **kwargs)