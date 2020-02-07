""" Daemonized WAVES system commands """
from __future__ import unicode_literals

import datetime
import logging
import os
import signal
import time
from itertools import chain

from daemons.prefab import run

import waves.core.exceptions
from waves.core.adaptors.exceptions import AdaptorException
from waves.core.adaptors.const import JobStatus
from waves.core.models import Job
from waves.core.settings import waves_settings

logger = logging.getLogger('waves.daemon')
LOG = logging.getLogger('daemons')


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
        LOG.info("Cleanup on exit")

    def preloop_callback(self):
        """
        Override this method if you want to do initialization before actual daemon process infinite loop
        """
        logger.debug("preloop_callback")
        LOG.info("Warming up on start")

    def run(self):
        """
        Method called upon 'start' command from daemon manager, must be overriden in actual job daemon subclass
        """
        try:
            self.preloop_callback()
            LOG.info("Starting daemon")
            while True:
                self.loop_callback()
        except (SystemExit, KeyboardInterrupt):
            # Normal exit getting a signal from the parent process
            pass
        except Exception as exc:
            # Something unexpected happened?
            LOG.error("Error starting deamon %s ", exc.__class__.__name__)
            logger.exception("Unexpected Exception %s", exc)

    def status(self):
        if self.pid < 0 or self.pid is None:
            LOG.warning("Process pid does not exists")
            if os.path.isfile(self.pidfile):
                try:
                    os.remove(self.pidfile)
                    LOG.info("Removed pid file %s", self.pidfile)
                except OSError:
                    LOG.error('Unable to remove pid file')
            return
        try:
            os.kill(self.pid, 0)
        except OSError:
            LOG.info("Process is stopped.")
        else:
            LOG.info("Process is running.")

    def stop(self):
        if self.pid is None:
            LOG.info('No process running')
        super(BaseRunDaemon, self).stop()


class JobQueueRunDaemon(BaseRunDaemon):
    """
    Dedicated command to summarize current WAVES specific settings
    """
    help = 'Managing WAVES job queue states'
    pidfile = os.path.join(waves_settings.DATA_ROOT, 'waves_queue.pid')
    pidfile_timeout = 5

    def loop_callback(self):
        """
        Very very simple daemon to monitor jobs queue.

        - Retrieve all current non terminated job, and process according to current status.
        - Jobs are run on a stateless process

        :return: None
        """
        jobs = Job.objects.prefetch_related('job_inputs'). \
            prefetch_related('outputs').filter(_status__lt=JobStatus.JOB_TERMINATED)
        if jobs.count() > 0:
            logger.info("Starting queue process with %i(s) unfinished jobs", jobs.count())
        for job in jobs:
            runner = job.adaptor
            if runner and logger.isEnabledFor(logging.DEBUG):
                logger.debug('[Runner]-------\n%s\n----------------', runner.dump_config())
            try:
                job.check_send_mail()
                logger.debug("Launching Job %s (adapter:%s)", job, runner)
                if job.status == JobStatus.JOB_CREATED:
                    job.run_prepare()
                    logger.debug("[PrepareJob] %s (adapter:%s)", job, runner)
                elif job.status == JobStatus.JOB_PREPARED:
                    logger.debug("[LaunchJob] %s (adapter:%s)", job, runner)
                    job.run_launch()
                elif job.status == JobStatus.JOB_COMPLETED:
                    job.run_results()
                    logger.debug("[JobExecutionEnded] %s (adapter:%s)", job.get_status_display(), runner)
                else:
                    job.run_status()
            except (waves.core.exceptions.WavesException, AdaptorException) as e:
                logger.error("Error Job %s (adapter:%s-state:%s): %s", job, runner, job.get_status_display(),
                             e.message)
            except IOError as exc:
                logger.error('IO error on job %s [%s]', job.slug, exc)
                job.status = JobStatus.JOB_ERROR
                job.save()
            except Exception as exc:
                logger.exception('Current job raised unrecoverable exception %s', exc)
                job.fatal_error(exc)
            finally:
                logger.info("Queue job terminated at: %s", datetime.datetime.now().strftime('%A, %d %B %Y %H:%M:%I'))
                job.check_send_mail()
                if runner is not None:
                    runner.disconnect()
        time.sleep(5)


class PurgeDaemon(BaseRunDaemon):
    help = 'Clean up old jobs '
    SLEEP_TIME = 86400
    pidfile_path = os.path.join(waves_settings.DATA_ROOT, 'waves_clean.pid')

    def loop_callback(self):
        logger.info("Purge job launched at: %s", datetime.datetime.now().strftime('%A, %d %B %Y %H:%M:%I'))
        date_anonymous = datetime.date.today() - datetime.timedelta(waves_settings.KEEP_ANONYMOUS_JOBS)
        date_registered = datetime.date.today() - datetime.timedelta(waves_settings.KEEP_REGISTERED_JOBS)
        anonymous = Job.objects.filter(client__isnull=True, updated__lt=date_anonymous)
        registered = Job.objects.filter(client__isnull=False, updated__lt=date_registered)
        for job in list(chain(*[anonymous, registered])):
            logger.info('Deleting job %s created on %s', job.slug, job.created)
            job.delete()
        logger.info("Purge job terminated at: %s", datetime.datetime.now().strftime('%A, %d %B %Y %H:%M:%I'))
        time.sleep(waves_settings.PURGE_WAIT)
