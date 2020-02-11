from waves_core.celery import app

import logging
import datetime
from itertools import chain

import waves.core.exceptions
from waves.core.adaptors.const import JobStatus
from waves.core.adaptors.exceptions import AdaptorException
from waves.core.models import Job


@app.task(name="job_queue")
def process_job_queue():
    """
    Very very simple daemon to monitor jobs queue.

    - Retrieve all current non terminated job, and process according to current status.
    - Jobs are run on a stateless process

    :return: None
    """
    logger = logging.getLogger()
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

@app.task(name="purge_jobs")
def purge_old_jobs():
    from waves.core.settings import waves_settings

    logger = logging.getLogger()

    logger.info("Purge job launched at: %s", datetime.datetime.now().strftime('%A, %d %B %Y %H:%M:%I'))
    date_anonymous = datetime.date.today() - datetime.timedelta(waves_settings.KEEP_ANONYMOUS_JOBS)
    date_registered = datetime.date.today() - datetime.timedelta(waves_settings.KEEP_REGISTERED_JOBS)
    anonymous = Job.objects.filter(client__isnull=True, updated__lt=date_anonymous)
    registered = Job.objects.filter(client__isnull=False, updated__lt=date_registered)
    for job in list(chain(*[anonymous, registered])):
        logger.info('Deleting job %s created on %s', job.slug, job.created)
        job.delete()
    logger.info("Purge job terminated at: %s", datetime.datetime.now().strftime('%A, %d %B %Y %H:%M:%I'))