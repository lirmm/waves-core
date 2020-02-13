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
