from __future__ import unicode_literals, absolute_import

import logging
import os
import tempfile

from waves.core.management.daemoncommand import DaemonCommand
from waves.core.management.runner import JobQueueRunDaemon

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
