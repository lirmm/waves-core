from __future__ import unicode_literals

import abc

from waves.adaptors.core.adaptor import JobAdaptor


class RemoteApiAdaptor(JobAdaptor):
    """ Base Class for remote API calls"""
    #: remote host port
    port = ''
    #: base remote api path
    api_base_path = ''
    #: remote endpoint
    api_endpoint = ''

    @property
    def init_params(self):
        base = super(RemoteApiAdaptor, self).init_params
        base.update(dict(port=self.port,
                         api_base_path=self.api_base_path,
                         api_endpoint=self.api_endpoint))
        return base

    @property
    def complete_url(self):
        """ Create complete url string for remote api"""
        url = "%s://%s" % (self.protocol, self.host)
        if self.port != '':
            url += ':%s' % self.port
        if self.api_base_path != '':
            url += '/%s' % self.api_base_path
        if self.api_endpoint != '':
            url += '/%s' % self.api_endpoint
        return url

    def connexion_string(self):
        return self.complete_url
