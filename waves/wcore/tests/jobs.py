from __future__ import unicode_literals

import logging
import os

from django.core import mail
from django.utils import timezone

import waves.wcore.adaptors.const
from waves.wcore.models import get_service_model, get_submission_model
from waves.wcore.settings import waves_settings as config
from waves.wcore.tests import BaseTestCase

logger = logging.getLogger(__name__)
Service = get_service_model()
Submission = get_submission_model()

logger = logging.getLogger(__name__)


class TestJobs(BaseTestCase):

    def test_jobs_signals(self):
        job = self.create_random_job()
        self.assertIsNotNone(job.title)
        self.assertEqual(job.outputs.count(), 4)
        self.assertTrue(os.path.isdir(job.working_dir))
        logger.debug('Job directories has been created %s ', job.working_dir)
        self.assertEqual(job.status, waves.wcore.adaptors.const.JOB_CREATED)
        self.assertEqual(job.job_history.count(), 1)
        job.message = "Test job Message"
        job.status = waves.wcore.adaptors.const.JOB_PREPARED
        job.save()
        self.assertGreaterEqual(job.job_history.filter(message__contains=job.message).all(), 0)
        job.delete()
        self.assertFalse(os.path.isdir(job.working_dir))
        logger.debug('Job directories has been deleted')

    def test_job_history(self):
        # TODO check messages sent to history
        job = self.create_random_job()
        job.job_history.create(message="Test Admin message", status=job.status, is_admin=True)
        job.job_history.create(message="Test public message", status=job.status)
        try:
            self.assertEqual(job.job_history.count(), 3)
            self.assertEqual(job.public_history.count(), 2)
        except AssertionError:
            logger.debug('All history %s', job.job_history.all())
            logger.debug('Public history %s', job.public_history.all())
            raise

    def test_mail_job(self):
        job = self.create_random_job()

        job.status_time = timezone.datetime.now()
        logger.debug("Job link: %s", job.link)
        logger.debug("Job notify: %s", job.notify)
        job.check_send_mail()
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[-1]
        self.assertTrue(job.service in sent_mail.subject)
        self.assertEqual(job.email_to, sent_mail.to[0])
        self.assertEqual(config.SERVICES_EMAIL, sent_mail.from_email)
        logger.debug('Mail subject: %s', sent_mail.subject)
        logger.debug('Mail from: %s', sent_mail.from_email)
        logger.debug('Mail content: \n%s', sent_mail.body)
        job.status = waves.wcore.adaptors.const.JOB_COMPLETED
        # job.save()
        job.check_send_mail()
        # no more mails
        self.assertEqual(len(mail.outbox), 1)

        job.status = waves.wcore.adaptors.const.JOB_TERMINATED
        # job.save()
        job.check_send_mail()
        self.assertEqual(len(mail.outbox), 2)
        sent_mail = mail.outbox[-1]
        logger.debug('Mail subject: %s', sent_mail.subject)
        logger.debug('Mail from: %s', sent_mail.from_email)
        logger.debug('Mail content: \n%s', sent_mail.body)
        job.status = waves.wcore.adaptors.const.JOB_ERROR
        # job.save()
        job.check_send_mail()
        # mail to user and mail to admin so +2
        self.assertEqual(len(mail.outbox), 4)
        sent_mail = mail.outbox[-1]
        logger.debug('Mail subject: %s', sent_mail.subject)
        logger.debug('Mail from: %s', sent_mail.from_email)
        logger.debug('Mail content: \n%s', sent_mail.body)
        job.status = waves.wcore.adaptors.const.JOB_CANCELLED
        # job.save()
        job.check_send_mail()
        self.assertEqual(len(mail.outbox), 5)
        sent_mail = mail.outbox[-1]
        logger.debug('Mail subject: %s', sent_mail.subject)
        logger.debug('Mail from: %s', sent_mail.from_email)
        logger.debug('Mail content: \n%s', sent_mail.body)
