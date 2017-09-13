""" Daemonized WAVES system commands """
from __future__ import unicode_literals

import datetime
import logging
import os
import signal
import tempfile
import time
from itertools import chain

from daemons.prefab import run

import waves.wcore.adaptors.const
import waves.wcore.exceptions
from waves.wcore.adaptors.exceptions import AdaptorException
from waves.wcore.models import Job, Submission
from waves.wcore.settings import waves_settings
from waves.wcore.settings import waves_settings as config

logger = logging.getLogger('waves.daemon')


class BaseRunDaemon(run.RunDaemon):

    def __init__(self, *args, **kwargs):
        super(BaseRunDaemon, self).__init__(*args, **kwargs)
        self._handlers = {
            signal.SIGTERM: [self.exit_callback],
            signal.SIGKILL: [self.exit_callback]
        }

    def loop_callback(self):
        """ Main loop executed by daemon """
        raise NotImplementedError('You must implement loop_callback method to define a daemon')

    def exit_callback(self):
        """
        Exit callback, called whenever process is manually stopped, or killed elsewhere.
        .. WARNING:
            If you plan to override this function, remember to always call parent method in order to terminate process
        """
        logger.debug("exit_callback")

    def preloop_callback(self):
        """
        Override this method if you want to do initialization before actual daemon process infinite loop
        """
        logger.debug("preloop_callback")

    def run(self):
        """
        Method called upon 'start' command from daemon manager, must be overriden in actual job daemon subclass
        """
        try:
            self.preloop_callback()
            logger.debug("Starting loopback...")
            while True:
                self.loop_callback()
        except (SystemExit, KeyboardInterrupt):
            # Normal exit getting a signal from the parent process
            pass
        except Exception as exc:
            # Something unexpected happened?
            logger.exception("Unexpected Exception %s", exc.message)


class JobQueueRunDaemon(BaseRunDaemon):
    """
    Dedicated command to summarize current WAVES specific settings
    """
    help = 'Managing WAVES job queue states'
    SLEEP_TIME = 2
    pidfile = os.path.join(tempfile.gettempdir(), 'waves_queue.pid')
    pidfile_timeout = 5

    def loop_callback(self):
        """
        Very very simple daemon to monitor jobs queue.

        - Retrieve all current non terminated job, and process according to current status.
        - Jobs are run on a stateless process

        .. todo::
            Implement this as separated forked processes for each jobs, inspired by Galaxy queue treatment.

        :return: Nothing
        """
        jobs = Job.objects.prefetch_related('job_inputs'). \
            prefetch_related('outputs').filter(_status__lt=waves.wcore.adaptors.const.JOB_TERMINATED)
        if jobs.count() > 0:
            logger.info("Starting queue process with %i(s) unfinished jobs", jobs.count())
        for job in jobs:
            runner = job.adaptor
            if runner and logger.isEnabledFor(logging.DEBUG):
                logger.debug('[Runner]-------\n%s\n----------------', runner.dump_config())
            try:
                job.check_send_mail()
                logger.debug("Launching Job %s (adaptor:%s)", job, runner)
                if job.status == waves.wcore.adaptors.const.JOB_CREATED:
                    job.run_prepare()
                    logger.debug("[PrepareJob] %s (adaptor:%s)", job, runner)
                elif job.status == waves.wcore.adaptors.const.JOB_PREPARED:
                    logger.debug("[LaunchJob] %s (adaptor:%s)", job, runner)
                    job.run_launch()
                elif job.status == waves.wcore.adaptors.const.JOB_COMPLETED:
                    job.run_results()
                    logger.debug("[JobExecutionEnded] %s (adaptor:%s)", job.get_status_display(), runner)
                else:
                    job.run_status()
            except (waves.wcore.exceptions.WavesException, AdaptorException) as e:
                logger.error("Error Job %s (adaptor:%s-state:%s): %s", job, runner, job.get_status_display(),
                             e.message)
            finally:
                logger.info("Queue job terminated at: %s", datetime.datetime.now().strftime('%A, %d %B %Y %H:%M:%I'))
                job.check_send_mail()
                if runner is not None:
                    runner.disconnect()
        logger.debug('Go to sleep for %i seconds' % self.SLEEP_TIME)
        time.sleep(self.SLEEP_TIME)


class PurgeDaemon(BaseRunDaemon):
    help = 'Clean up old jobs '
    SLEEP_TIME = 86400
    pidfile_path = os.path.join(waves_settings.DATA_ROOT, 'waves_clean.pid')

    def loop_callback(self):
        logger.info("Purge job launched at: %s", datetime.datetime.now().strftime('%A, %d %B %Y %H:%M:%I'))
        date_anonymous = datetime.date.today() - datetime.timedelta(config.KEEP_ANONYMOUS_JOBS)
        date_registered = datetime.date.today() - datetime.timedelta(config.KEEP_REGISTERED_JOBS)
        anonymous = Job.objects.filter(client__isnull=True, updated__lt=date_anonymous)
        registered = Job.objects.filter(client__isnull=False, updated__lt=date_registered)
        for job in list(chain(*[anonymous, registered])):
            logger.info('Deleting job %s created on %s', job.slug, job.created)
            job.delete()
        logger.info("Purge job terminated at: %s", datetime.datetime.now().strftime('%A, %d %B %Y %H:%M:%I'))
