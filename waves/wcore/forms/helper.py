from __future__ import unicode_literals


class WFormHelper:

    def __init__(self, *args, **kwargs):
        pass

    def set_layout(self, service_input, form=None):
        raise NotImplementedError()

    def init_layout(self, fields):
        pass

    def end_layout(self):
        pass
