
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


import datetime
import logging
from itertools import chain

from waves.core.models import Job

logger = logging.getLogger('waves.cron')


def purge_old_jobs():
    from waves.core.settings import waves_settings

    logger.info("Purge job launched at: %s", datetime.datetime.now().strftime('%A, %d %B %Y %H:%M:%I'))
    date_anonymous = datetime.date.today() - datetime.timedelta(waves_settings.KEEP_ANONYMOUS_JOBS)
    date_registered = datetime.date.today() - datetime.timedelta(waves_settings.KEEP_REGISTERED_JOBS)
    anonymous = Job.objects.filter(client__isnull=True, updated__lt=date_anonymous)
    registered = Job.objects.filter(client__isnull=False, updated__lt=date_registered)
    for job in list(chain(*[anonymous, registered])):
        logger.info('Deleting job %s created on %s', job.slug, job.created)
        job.delete()
    logger.info("Purge job terminated at: %s", datetime.datetime.now().strftime('%A, %d %B %Y %H:%M:%I'))
