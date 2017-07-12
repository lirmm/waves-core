from __future__ import unicode_literals

import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template

from waves.core.settings import waves_settings as config

logger = logging.getLogger(__name__)


class JobMailer(object):
    """
    JobMailer, class in charge for sending templated emails to Jobs submitter, according to status changes.

    - **params**:
        :param: Job related job to send email for

    """
    _template_subject = None
    _template_mail = None

    def get_context_data(self):
        return {'APP_NAME': config.APP_NAME,
                'contact': config.SERVICES_EMAIL}

    @property
    def mail_activated(self):
        """
        Check if email are activated for this job's service, and if globally enabled in configuration

        :return: True if mail are to be sent, False either
        :rtype: bool
        """
        return config.NOTIFY_RESULTS

    def _send_job_mail(self, job, template, subject=None):
        """ Check if send mail is needed, in such case, create a template email and... send it to specified client

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        if self.mail_activated and job.notify:
            context = self.get_context_data()
            context['job'] = job
            mail_subject = "Waves Job [%s]" % job.title if subject is None else subject
            try:
                message = get_template(template_name=template).render(context)
                msg = EmailMessage(subject=mail_subject, body=message, to=[job.email_to],
                                   from_email=config.SERVICES_EMAIL)
                msg.content_subtype = 'html'
                msg.send(fail_silently=not settings.DEBUG)
            except Exception as e:
                logger.exception("Failed to send mail to %s from %s :%s", job.email_to, config.SERVICES_EMAIL, e)
        else:
            logger.info('Mail not sent to %s, mails are not activated', job.email_to)
            return 0

    def send_job_submission_mail(self, job):
        """
        Send Job Submission confirmation email

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(job, "waves/emails/job_submitted.html")

    def send_job_completed_mail(self, job):
        """
        Send Job completed email

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(job, "waves/emails/job_completed.html")

    def send_job_error_email(self, job):
        """
        Send Job error email

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(job, "waves/emails/job_error.html")

    def send_job_cancel_email(self, job):
        """
        Send Job cancelled email

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(job, "waves/emails/job_cancelled.html")

    def send_job_admin_error(self, job):
        """ Admin mail to notify run error
        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(job, "waves/emails/job_admin_error.html")
