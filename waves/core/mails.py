from __future__ import unicode_literals

import logging

from django.core.mail import EmailMessage
from django.template.loader import get_template

from waves.core.adaptors.const import JobStatus
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

    def _send_job_mail(self, job, template, subject=None, force=False):
        """ Check if send mail is needed, in such case, create a template email and... send it to specified client

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        if (self.mail_activated and job.notify) or force:
            context = self.get_context_data()
            context['job'] = job
            mail_subject = "[WAVES - %s] -- %s -- " % (
                job.title, job.get_status_display()) if subject is None else subject
            try:
                message = get_template(template_name=template).render(context)
                msg = EmailMessage(subject=mail_subject, body=message, to=[job.email_to],
                                   from_email=config.SERVICES_EMAIL)
                msg.send(fail_silently=True)
                job.job_history.create(message='Notification email sent', status=job.status, is_admin=True)
            except Exception as e:
                job.job_history.create(message='Notification email not sent %s' % e.message, status=job.status,
                                       is_admin=True)
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
        return self._send_job_mail(job, "waves/emails/job_submitted.tpl")

    def send_job_completed_mail(self, job):
        """
        Send Job completed email

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(job, "waves/emails/job_completed.tpl")

    def send_job_error_email(self, job):
        """
        Send Job error email

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(job, "waves/emails/job_error.tpl")

    def send_job_warning_email(self, job):
        """
        Send Job error email

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(job, "waves/emails/job_warning.tpl")

    def send_job_cancel_email(self, job):
        """
        Send Job cancelled email

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        return self._send_job_mail(job, "waves/emails/job_cancelled.tpl")

    def send_job_admin_error(self, job):
        """ Admin mail to notify run error
        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        job.notify = True
        job.email_to = config.ADMIN_EMAIL
        return self._send_job_mail(job, "waves/emails/job_admin_error.tpl", subject="Waves Error", force=True)

    def check_send_mail(self, job):
        """According to job status, check needs for sending notification emails

        :return: the nmmber of mail sent (should be one)
        :rtype: int
        """
        if job.status != job.status_mail and job.status == JobStatus.JOB_ERROR:
            self.send_job_admin_error(job)
        if config.NOTIFY_RESULTS and job.notify:
            if job.email_to is not None and job.status != job.status_mail:
                # should send a email
                try:
                    nb_sent = 0
                    if job.status == JobStatus.JOB_CREATED:
                        nb_sent = self.send_job_submission_mail(job)
                    elif job.status == JobStatus.JOB_TERMINATED:
                        nb_sent = self.send_job_completed_mail(job)
                    elif job.status == JobStatus.JOB_ERROR:
                        nb_sent = self.send_job_error_email(job)
                    elif job.status == JobStatus.JOB_WARNING:
                        nb_sent = self.send_job_warning_email(job)
                    elif job.status == JobStatus.JOB_CANCELLED:
                        nb_sent = self.send_job_cancel_email(job)
                    # Avoid resending emails when last status mail already sent
                    job.status_mail = job.status
                    return nb_sent
                except Exception as e:
                    logger.error('Mail error: %s %s', e.__class__.__name__, e.message)
                    pass
                finally:
                    job.save()
            elif not job.email_to:
                logger.warn('Job [%s] email not sent to %s', job.slug, job.email_to)
        else:
            logger.debug('Jobs notification are not activated')
