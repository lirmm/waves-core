from abc import ABC

from core.management import SubcommandDispatcher
from core.management import JobQueueCommand, PurgeDaemonCommand
from core.management import CleanUpCommand, ImportCommand, DumpConfigCommand

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
