"""
Extended DaemonRunner class (from python-daemon):
- add `status` command
- add `argv` override to __init__ arguments
- implement base `run()` method, which launch `loop_callback()`, on exit run `exit_callback()`

"""
from __future__ import unicode_literals

import logging
import signal

import lockfile
import psutil
from daemon.runner import DaemonRunner as BaseDaemonRunner, DaemonRunnerStopFailureError, \
    DaemonRunnerStartFailureError, emit_message

logger = logging.getLogger(__name__)


class DaemonRunner(BaseDaemonRunner):
    """ Override base DaemonRunner from python-daemon in order to add 'Status' method

    """
    LOCK_ERROR = "Unable to acquire lock: process may be already running ?"
    START_ERROR = "Unable to start %s"
    STOP_ERROR = "Unable to stop %s"
    STATUS_STOPPED = "Stopped"
    STATUS_RUNNING = "Running"
    STATUS_UNKNOWN = "Unknown"
    _verbose = True

    def _status(self):
        try:
            running = psutil.pid_exists(self.pidfile.read_pid())
        except (OSError, TypeError):
            emit_message(self.STATUS_UNKNOWN)
            return self.STATUS_UNKNOWN
        else:
            if running:
                emit_message(self.STATUS_RUNNING)
                return self.STATUS_RUNNING
            else:
                emit_message(self.STATUS_STOPPED)
                return self.STATUS_STOPPED

    def _start(self):
        try:
            super(DaemonRunner, self)._start()
        except DaemonRunnerStartFailureError as exc:
            emit_message(self.START_ERROR % exc.message)
        except lockfile.LockTimeout as exc:
            emit_message(self.LOCK_ERROR)

    def _stop(self):
        try:
            pid = self.pidfile.read_pid()
            super(DaemonRunner, self)._stop()
            emit_message("Process %i stopped " % pid)
        except DaemonRunnerStopFailureError as exc:
            emit_message(self.STOP_ERROR % exc.message)

    def _restart(self):
        super(DaemonRunner, self)._restart()

    action_funcs = {
        'start': _start,
        'stop': _stop,
        'restart': _restart,
        'status': _status
    }

    def __init__(self, app, **options):
        """ Set up the parameters of a new runner.
            **Override base DaemonRunner in order to provide specific args upon creation**

            :param app: The application instance; see below.
            :return: ``None``.

            The `app` argument must have the following attributes:

            * `stdin_path`, `stdout_path`, `stderr_path`: Filesystem paths
              to open and replace the existing `sys.stdin`, `sys.stdout`,
              `sys.stderr`.

            * `pidfile_path`: Absolute filesystem path to a file that will
              be used as the PID file for the daemon. If ``None``, no PID
              file will be used.

            * `pidfile_timeout`: Used as the default acquisition timeout
              value supplied to the runner's PID lock file.

            * `run`: Callable that will be invoked when the daemon is
              started.

            """
        super(DaemonRunner, self).__init__(app)
        # preserve file related loggers handlers
        self.daemon_context.files_preserve = self.getLogFilesHandles(logger)
        self.daemon_context.detach_process = True
        self.daemon_context.working_directory = options.get('work_dir')
        self.daemon_context.signal_map[signal.SIGTERM] = app.exit_callback

    def getLogFilesHandles(self, logger):
        handles = []
        for handler in logger.handlers:
            handles.append(handler.stream.fileno())
        if logger.parent:
            handles += self.getLogFilesHandles(logger.parent)
        return handles
