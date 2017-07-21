from __future__ import unicode_literals


class WFormHelper(object):

    def set_layout(self, service_input):
        raise NotImplementedError()

    def init_layout(self, fields):
        pass

    def end_layout(self):
        pass
