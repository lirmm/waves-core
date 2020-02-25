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
import logging

logger = logging.getLogger(__name__)


class WavesException(Exception):
    """
    Waves base exception class, simply log exception in standard web logs
    TODO: This class may be obsolete depending of running / logging configuration
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        logger.exception('[%s] - %s', self.__class__.__name__, self)


class ExportError(Exception):
    """ Export 'Error'"""
    pass