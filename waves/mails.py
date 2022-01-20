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

from django.core.mail import EmailMessage
from django.template.loader import get_template

from waves.settings import waves_settings
from waves.core.const import JobStatus

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
        return {'APP_NAME': waves_settings.APP_NAME,
                'contact': waves_settings.SERVICES_EMAIL}

    @property
    def mail_activated(self):
        """
        Check if email are activated for this job's service, and if globally enabled in waves_settingsuration

        :return: True if mail are to be sent, False either
        :rtype: bool
        """
        return waves_settings.NOTIFY_RESULTS

    def _send_job_mail(self, job, template, force=False):
        """ Check if send mail is needed, in such case, create a template email and... send it to specified client

        :return: the number of mail sent, should be 0 or 1
        :rtype: int
        """
        if (self.mail_activated and job.notify) or force:
            context = self.get_context_data()
            context['job'] = job
            mail_subject = "[WAVES][%s] - %s - %s - " % (job.service, job.title, job.get_status_display())
            try:
                message = get_template(template_name=template).render(context)
                msg = EmailMessage(subject=mail_subject, body=message, to=[job.email_to],
                                   from_email=waves_settings.SERVICES_EMAIL)
                logger.debug("Sending {} message {}  to {}".format(msg.subject, msg.body, msg.to))
                msg.send(fail_silently=False)
                job.job_history.create(message='Notification email sent', status=job.status, is_admin=True)
            except Exception as e:
                job.job_history.create(message='Notification email not sent %s' % e.message, status=job.status,
                                       is_admin=True)
                logger.exception("Failed to send mail to %s from %s :%s", job.email_to, waves_settings.SERVICES_EMAIL, e)
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
        job.email_to = waves_settings.ADMIN_EMAIL
        return self._send_job_mail(job, "waves/emails/job_admin_error.tpl", force=True)

    def check_send_mail(self, job):
        """According to job status, check needs for sending notification emails

        :return: the nmmber of mail sent (should be one)
        :rtype: int
        """
        if job.status != job.status_mail and job.status == JobStatus.JOB_ERROR:
            self.send_job_admin_error(job)
        if waves_settings.NOTIFY_RESULTS and job.notify:
            if job.email_to is not None and job.status != job.status_mail:
                # should send a email
                try:
                    nb_sent = 0
                    if job.status == JobStatus.JOB_CREATED:
                        logger.debug('JOB_CREATED mail: {}'.format(nb_sent))
                        nb_sent = self.send_job_submission_mail(job)
                    elif job.status == JobStatus.JOB_FINISHED:
                        logger.debug('JOB_FINISHED mail: {}'.format(nb_sent))
                        nb_sent = self.send_job_completed_mail(job)
                    elif job.status == JobStatus.JOB_ERROR:
                        logger.debug('JOB_ERROR mail: {}'.format(nb_sent))
                        nb_sent = self.send_job_error_email(job)
                    elif job.status == JobStatus.JOB_WARNING:
                        logger.debug('JOB_WARNING mail: {}'.format(nb_sent))
                        nb_sent = self.send_job_warning_email(job)
                    elif job.status == JobStatus.JOB_CANCELLED:
                        logger.debug('JOB_CANCELLED mail: {}'.format(nb_sent))
                        nb_sent = self.send_job_cancel_email(job)
                    # Avoid resending emails when last status mail already sent
                    job.status_mail = job.status
                    logger.debug('Mails sent: {}'.format(nb_sent))
                    return nb_sent
                except Exception as e:
                    logger.error('Mail error: %s %s', e.__class__.__name__, e.message)
                    pass
                finally:
                    job.save()
            elif not job.email_to:
                logger.warning('Job [%s] email not sent to %s', job.slug, job.email_to)
        else:
            logger.debug('Jobs notification are not activated')