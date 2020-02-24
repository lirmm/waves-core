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


class AdaptorException(BaseException):
    """ Base adapter exception class, should be raise upon specific adapter class exception catch
    this exception class is supposed to be catched
    """
    pass


class AdaptorConnectException(AdaptorException):
    """
    adapter Connection Error
    """
    pass


class AdaptorExecException(AdaptorException):
    """
    adapter execution error
    """
    pass


class AdaptorNotAvailableException(AdaptorExecException):
    pass


class AdaptorJobException(AdaptorException):
    """
    adapter JobRun Exception
    """
    pass


class AdaptorNotReady(AdaptorException):
    """ adapter is not properly initialized to be used """
    pass


class AdaptorInitError(AdaptorException):
    """ Each adapter expects some attributes for initialization, this exception should be raised when some mandatory
    parameters are missing
    """
    pass


class ImporterException(AdaptorException):
    pass


class UnhandledException(ImporterException):
    base_msg = ''

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.message = self.base_msg + self.message


class UnhandledAttributeException(UnhandledException):
    base_msg = "Unmanaged Attribute: "

    def __init__(self, *args, **kwargs):
        super(UnhandledAttributeException, self).__init__(*args, **kwargs)


class UnhandledAttributeTypeException(UnhandledException):
    base_msg = "Unmanaged Type: "

    def __init__(self, *args, **kwargs):
        super(UnhandledAttributeTypeException, self).__init__(*args, **kwargs)


class UnhandledInputTypeException(UnhandledException):
    base_msg = "Unmanaged Input: "

    def __init__(self, *args, **kwargs):
        super(UnhandledInputTypeException, self).__init__(*args, **kwargs)


class JobPrepareException(AdaptorJobException):
    """Preparation process errors """
    pass