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
from .base import WavesException


class RunnerException(WavesException):
    """
    Base Exception class for all Runner related errors
    """

    def __init__(self, *args, **kwargs):
        super(RunnerException, self).__init__(*args, **kwargs)


class RunnerNotInitialized(RunnerException):
    pass


class RunnerUnexpectedInitParam(RunnerException, KeyError):
    pass


class RunnerConnectionError(RunnerException):
    def __init__(self, reason, msg=''):
        message = reason
        if msg != '':
            message = '%s %s' % (msg, message)
        super(RunnerException, self).__init__(message)


class RunnerNotReady(RunnerException):
    pass