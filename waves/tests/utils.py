from __future__ import unicode_literals
from os.path import join, dirname, isfile, realpath


def assertion_tracker(func):

    def method_wrapper(method):
        def wrapped_method(test, *args, **kwargs):
            return method(test, *args, **kwargs)

        # Must preserve method name so nose can detect and report tests by
        # name.
        wrapped_method.__name__ = method.__name__
        return wrapped_method

    return method_wrapper


def get_sample_dir():
    return join(dirname(dirname(realpath(__file__))), 'data', 'sample')
