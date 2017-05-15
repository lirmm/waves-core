""" WAVES Importers dedicated Exceptions """
from __future__ import unicode_literals

__all__ = ['UnManagedAttributeException', 'UnManagedAttributeTypeException', 'UnmanagedInputTypeException']


class UnmanagedException(BaseException):
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

