from __future__ import unicode_literals

from django.conf import settings
from mail_templated import send_mail
from constance import config


class JobMailer(object):
    """
    JobMailer, class in charge for sending templated emails to Jobs submitter, according to status changes.

    - **params**:
        :param: Job related job to send email for

    """
    _template_subject = None
    _template_mail = None

    def __init__(self, job):
        super(JobMailer, self).__init__()
        self.job = job

    def get_context_data(self):
        return {'job': self.job,
                'WAVES_APP_NAME': config.WAVES_APP_NAME,
                'contact': config.WAVES_SERVICES_EMAIL}

    @property
    def mail_activated(self):
        """
        Check if email are activated for this job's service, and if globally enabled in configuration

        :return: True if mail are to be sent, False either
        :rtype: bool
        """
        return config.WAVES_NOTIFY_RESULTS and self.job.service.email_on

    def _send_job_mail(self, template, subject="Your Job"):
        """ Check if send mail is needed, in such case, create a template email and... send it to specified client

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        if self.mail_activated:
            context = self.get_context_data()
            return send_mail(template_name=template, context=context, from_email=config.WAVES_SERVICES_EMAIL,
                             recipient_list=[self.job.email_to], subject=subject,
                             fail_silently=not settings.DEBUG)
        else:
            # No mail sent since not activated (keep value returned at same type than send_mail
            return 0

    def send_job_submission_mail(self):
        """
        Send Job Submission confirmation email

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(template="emails/job_submitted.html")

    def send_job_completed_mail(self):
        """
        Send Job completed email

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(template="emails/job_completed.html")

    def send_job_error_email(self):
        """
        Send Job error email

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(template="emails/job_error.html")

    def send_job_cancel_email(self):
        """
        Send Job cancelled email

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(template="emails/job_cancelled.html")

    def send_job_admin_error(self):
        """ Admin mail to notify run error
        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(template="emails/job_admin_error.html")