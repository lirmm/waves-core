import logging
import os

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from waves.core.adaptors.const import JobStatus
from waves.core.tests.base import WavesTestCaseMixin

logger = logging.getLogger(__name__)

User = get_user_model()


class JobsTestCase(TestCase, WavesTestCaseMixin):
    fixtures = ("users",)

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
            logger.debug("History timestamp %s", localtime(history.timestamp))
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

    def testJobsSignals(self):
        print(User.objects.all())
        job = self.create_random_job()
        self.assertIsNotNone(job.title)
        self.assertEqual(job.outputs.count(), 4)
        job.logger.debug("Test Log message")
        self.assertTrue(os.path.isdir(job.working_dir))
        logger.warning('Job directories has been created %s ', job.working_dir)
        self.assertEqual(job.status, JobStatus.JOB_CREATED)
        self.assertEqual(job.job_history.count(), 1)
        job.message = "Test job Message"
        job.status = JobStatus.JOB_PREPARED
        job.save()
        self.assertGreaterEqual(job.job_history.filter(message__contains=job.message).count(), 0)
        work_dir = job.working_dir
        job.delete()
        self.assertFalse(os.path.isdir(work_dir))
        logger.debug('Job directories has been deleted')

    def test_job_history(self):
        job = self.create_random_job()
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
        user = User.objects.create(username='TestDomain', is_active=True)
        user.waves_user.domain = 'https://waves.test.com'
        user.waves_user.save()
        job = self.create_random_job(user=user)

        logger.info("Job link: %s", job.link)
        logger.debug("Job notify: %s", job.notify)
        job.check_send_mail()
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[-1]
        self.assertTrue(job.service in sent_mail.subject)
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
