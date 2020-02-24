"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the GNU GPL v3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       https://www.gnu.org/licenses/gpl-3.0.en.html
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
from abc import ABC

from waves.core.adaptors import JobAdaptor


# noinspection PyAbstractClass
class PublicApiAdaptor(JobAdaptor):
    """ Base Class for remote public API calls"""
    port = ''
    api_endpoint = ''
    api_base_path = ''

    def __init__(self, command=None, protocol='http', host="localhost", port='', api_base_path='', api_endpoint='',
                 **kwargs):
        super(PublicApiAdaptor, self).__init__(command, protocol, host, **kwargs)
        self.port = port
        self.api_endpoint = api_endpoint
        self.api_base_path = api_base_path

    @property
    def init_params(self):
        base = super(PublicApiAdaptor, self).init_params
        base.update(dict(port=self.port,
                         api_base_path=self.api_base_path,
                         api_endpoint=self.api_endpoint))
        return base

    @property
    def complete_url(self):
        """ Create complete url string for remote api"""
        url = "%s://%s" % (self.protocol, self.host)
        if self.port is not None and self.port != '' and self.port != '80':
            url += ':%s' % self.port
        if self.api_base_path is not None and self.api_base_path != '':
            url += '/%s' % self.api_base_path
        if self.api_endpoint is not None and self.api_endpoint != '':
            url += '/%s' % self.api_endpoint
        return url

    def connexion_string(self):
        return self.complete_url


class ApiKeyAdaptor(PublicApiAdaptor, ABC):
    """
    Authenticated api calls
    """
    _api_get_key = 'app_key'

    def __init__(self, command=None, protocol='http', host="localhost", port='', api_base_path='', api_endpoint='',
                 app_key=None, **kwargs):
        super(ApiKeyAdaptor, self).__init__(command, protocol, host, port, api_base_path, api_endpoint, **kwargs)
        self.app_key = app_key

    @property
    def init_params(self):
        base = super(ApiKeyAdaptor, self).init_params
        base.update(dict(app_key=self.app_key))
        return base
