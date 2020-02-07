import logging
import os
from os.path import join

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail

from waves.core.adaptors.const import JobStatus
from waves.core.models import get_service_model, get_submission_model
from waves.core.tests.base import BaseTestCase

logger = logging.getLogger(__name__)
Service = get_service_model()
Submission = get_submission_model()
User = get_user_model()


class BasicTestCase(BaseTestCase):
    def test_overridden_config(self):
        from waves.core.settings import waves_settings
        self.assertEqual(waves_settings.JOB_BASE_DIR, join(settings.BASE_DIR, 'tests', 'data', 'jobs'))
        self.assertEqual(waves_settings.ADMIN_EMAIL, 'admin@test-waves.com')


class JobsTestCase(BaseTestCase):

    def test_jobs_signals(self):
        job = self.create_random_job()
        self.assertIsNotNone(job.title)
        self.assertEqual(job.outputs.count(), 4)
        self.assertTrue(os.path.isdir(job.working_dir))
        job.logger.debug("Test Log message")
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

        job.status = JobStatus.JOB_TERMINATED
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
