from __future__ import unicode_literals

from waves.core.adaptors.exceptions import AdaptorNotReady


def check_ready(func):
    def inner(self, *args, **kwargs):
        if not all(
                [value is not None for init_param, value in self.init_params.items() if init_param in self._required]):
            # search missing values
            raise AdaptorNotReady(
                "Missing required parameter(s) for initialization: %s " %
                [init_param for init_param, value in
                 self.init_params.items() if
                 value is None and init_param in self._required])
        else:
            return func(self, *args, **kwargs)

    return inner
