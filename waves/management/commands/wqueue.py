import logging
import os
import tempfile

from waves.management.command import DaemonCommand
from waves.management.runner import JobQueueRunDaemon

logger = logging.getLogger('waves.daemon')


class Command(DaemonCommand):
    """
    Dedicated command to summarize current WAVES specific settings
    """
    help = 'Managing WAVES job queue states'
    SLEEP_TIME = 2
    pidfile = os.path.join(tempfile.gettempdir(), 'waves_queue.pid')
    pidfile_timeout = 5
    _class = JobQueueRunDaemon
