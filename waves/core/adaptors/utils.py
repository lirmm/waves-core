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
from waves.core.exceptions import AdaptorNotReady


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
