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

from waves.management.base import SubcommandDispatcher
from waves.management.command import JobQueueCommand, PurgeDaemonCommand
from waves.management.subcommands import CleanUpCommand, ImportCommand, DumpConfigCommand

CLEAN = 'clean'
CONFIG = 'config'
DUMP = 'dump'
LOAD = 'load'
QUEUE = 'queue'
PURGE = 'purge'
SHOWURLS = 'show_urls'


class Command(SubcommandDispatcher, ABC):
    """ WAVES dedicated administration Django subcommand line interface (./manage.py) """
    help = 'WAVES Administration dedicated commands: type manage.py waves <sub_command> --help for sub-commands help'
    command_list = (CLEAN, CONFIG, LOAD, SHOWURLS)

    def _subcommand(self, name):
        if name == CLEAN:
            return CleanUpCommand()
        elif name == QUEUE:
            return JobQueueCommand()
        elif name == LOAD:
            return ImportCommand()
        elif name == CONFIG:
            return DumpConfigCommand()
        elif name == PURGE:
            return PurgeDaemonCommand()
        else:
            return None

    def _subcommand_names(self):
        return self.command_list
