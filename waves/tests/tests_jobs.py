"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the GNU GPL v3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       https://www.gnu.org/licenses/gpl-3.0.en.html
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import logging
import random
import time
from os.path import isfile

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from waves.core.const import JobStatus
from .base import sample_job, bootstrap_runners, bootstrap_services, WavesTestCaseMixin

logger = logging.getLogger(__name__)

User = get_user_model()


class JobsTestCase(TestCase, WavesTestCaseMixin):
    fixtures = ("accounts.json",)
    services = []
    runners = []
    user = None

    def run_job_workflow(self, job):
        """ Run a full complete job workflow, you should call this method catching "AssertionError" to get
        error messages in your tests
        """
        logger.info('Starting workflow process for job %s', job)
        self.assertTrue(job.job_history.count() == 1,
                        "Wrong job history count %s (expected 1)" % job.job_history.count())
        job.run_prepare()
        time.sleep(3)
        self.assertTrue(job.status == JobStatus.JOB_PREPARED,
                        "Wrong job status %s (expected %s) " % (job.status, JobStatus.JOB_PREPARED))
        job.run_launch()
        time.sleep(3)
        logger.debug('Remote Job ID %s', job.remote_job_id)
        self.assertTrue(job.status == JobStatus.JOB_QUEUED,
                        "Wrong job status %s (expected %s) " % (job.status, JobStatus.JOB_QUEUED))
        for ix in range(100):
            job_state = job.run_status()
            logger.info(u'Current job state (%i) : %s ', ix, job.get_status_display())
            if job_state >= JobStatus.JOB_COMPLETED:
                logger.info('Job state ended to %s ', job.get_status_display())
                break
            time.sleep(3)
        if job.status in (JobStatus.JOB_COMPLETED, JobStatus.JOB_FINISHED):
            # Get job run details
            job.retrieve_run_details()
            time.sleep(3)
            history = job.job_history.first()
            logger.debug("History timestamp %s", time.localtime(history.timestamp))
            self.assertTrue(job.results_available, "Job results are not available")
            for output_job in job.outputs.all():
                # TODO reactivate job output verification as soon as possible
                if not isfile(output_job.file_path):
                    logger.warning("Job <<%s>> did not output expected %s (%s) ",
                                   job.title, output_job.value, output_job.file_path)
                    self.fail('Expected output not present')
                else:
                    logger.info("Expected output file found : %s ", output_job.file_path)
            self.assertTrue(job.status == JobStatus.JOB_FINISHED)
            self.assertEqual(job.exit_code, 0)
            job.delete()
        else:
            logger.warning('problem with job status %s', job.get_status_display())
            self.fail("Job failed")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.services = bootstrap_services()
        cls.runners = bootstrap_runners()
        cls.user = User.objects.create(username='TestDomain', is_active=True)
        cls.user.waves_user.domain = 'https://waves.test.com'
        cls.user.waves_user.save()

    def test_job_history(self):
        job = sample_job(service=random.choice(self.services), user=self.user)
        job.logger.info("Test log message")
        job.job_history.create(message="Test Admin message", status=job.status, is_admin=True)
        job.job_history.create(message="Test public message", status=job.status)
        try:
            self.assertEqual(job.job_history.count(), 3)
            self.assertEqual(job.public_history.count(), 2)
        except AssertionError:
            logger.debug('All history %s', job.job_history.all())
            logger.debug('Public history %s', job.public_history.all())
            raise
        job.delete()

    def test_mail_job(self):

        job = sample_job(service=random.choice(self.services), user=self.user)

        logger.info("Job link: %s", job.link)
        logger.debug("Job notify: %s", job.notify)
        job.check_send_mail()
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[-1]
        self.assertTrue(job.service in sent_mail.subject)
        self.assertTrue(job.get_status_display() in sent_mail.subject)
        self.assertEqual(job.email_to, sent_mail.to[0])
        logger.debug('Mail subject: %s', sent_mail.subject)
        logger.debug('Mail from: %s', sent_mail.from_email)
        logger.debug('Mail content: \n%s', sent_mail.body)
        job.status = JobStatus.JOB_COMPLETED
        # job.save()
        job.check_send_mail()
        # no more mails
        self.assertEqual(len(mail.outbox), 1)

        job.status = JobStatus.JOB_FINISHED
        # job.save()
        job.check_send_mail()
        self.assertEqual(len(mail.outbox), 2)
        sent_mail = mail.outbox[-1]
        logger.debug('Mail subject: %s', sent_mail.subject)
        logger.debug('Mail from: %s', sent_mail.from_email)
        logger.debug('Mail content: \n%s', sent_mail.body)
        job.status = JobStatus.JOB_ERROR
        # job.save()
        job.check_send_mail()
        # mail to user and mail to admin so +2
        self.assertEqual(len(mail.outbox), 4)
        sent_mail = mail.outbox[-1]
        logger.debug('Mail subject: %s', sent_mail.subject)
        logger.debug('Mail from: %s', sent_mail.from_email)
        logger.debug('Mail content: \n%s', sent_mail.body)
        job.status = JobStatus.JOB_CANCELLED
        # job.save()
        job.check_send_mail()
        self.assertEqual(len(mail.outbox), 5)
        sent_mail = mail.outbox[-1]
        logger.debug('Mail subject: %s', sent_mail.subject)
        logger.debug('Mail from: %s', sent_mail.from_email)
        logger.debug('Mail content: \n%s', sent_mail.body)
        job.delete()
