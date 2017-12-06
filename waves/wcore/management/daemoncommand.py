import logging

from django.core.management.base import BaseCommand, CommandError


class DaemonCommand(BaseCommand):
    """
    Run a management command as a daemon.

    Subclass this and override the `loop_callback` method with the code the
    daemon process should run. Optionally, override `exit_callback` with
    code to run when the process is stopped.

    Alternatively, if your code has more complex setup/shutdown requirements,
    override `handle_noargs` along the lines of the basic version here.

    Pass one of --start, --stop, --restart or --status to work as a daemon.
    Otherwise, the command will run as a standard application.
    """

    # Django command params
    requires_model_validation = True
    # parameters python-daemon app
    stdin_path = '/dev/null'
    stdout_path = '/dev/stdout'
    stderr_path = '/dev/stderr'
    work_dir = '/'
    # pid configuration
    pidfile = '/tmp/daemon_command.pid'
    pidfile_timeout = 5
    # logs parameters defaults
    log_backup_count = 5
    log_max_bytes = 5 * 1024 * 1024
    log_file = '/tmp/daemon_command.log'
    log_level = logging.DEBUG
    _class = None
    action = None

    def add_arguments(self, parser):
        """
        Add options to daemon command, compatible for Django version >= 1.8
        :param parser: current Command parser
        :return: Nothing
        """
        parser.add_argument('action', choices=('start', 'stop', 'restart', 'status'), action="store",
                            help="Queue action")
        parser.add_argument('--pidfile', action='store', dest='pidfile', default=self.pidfile,
                            help='PID absolute filename.')
        parser.add_argument('--logfile', action='store', dest='log_file', default=self.log_file,
                            help='Path to log file')
        parser.add_argument('--loglevel', action='store', dest='log_file', default=self.log_level,
                            help='Path to log file')

    def handle(self, **options):
        """
        Handle commands for a daemon (--start|--stop|--restart|--status)
        :param options: list of possible django command options
        :return: Nothing
        """
        try:
            self.action = options.pop('action')
            logging.basicConfig(filename=self.log_file, level=self.log_level)
            if self._class is None:
                raise CommandError('You must set the destination Daemon class')
            d = self._class(pidfile=self.pidfile)
            getattr(d, self.action)()
        except KeyError:
            raise CommandError('You must specify an action with this command')
