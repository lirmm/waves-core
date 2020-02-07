
"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
from __future__ import unicode_literals

import logging
import datetime

import waves.core.exceptions
from waves.core.adaptors.const import JobStatus
from waves.core.adaptors.exceptions import AdaptorException
from waves.core.models import Job

logger = logging.getLogger('waves.cron')


def process_job_queue():
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
