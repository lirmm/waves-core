from django.db import models, IntegrityError

from waves.core.models.managers import JobHistoryManager, JobAdminHistoryManager
from waves.core.adaptors.const import JobStatus


class JobHistory(models.Model):
    """ Represents a job status history event
    """

    class Meta:
        ordering = ['-timestamp', '-status']
        unique_together = ('job', 'timestamp', 'status', 'is_admin')
        db_table = 'wcore_jobhistory'

    objects = JobHistoryManager()
    #: Related :class:`waves.core.models.jobs.Job`
    job = models.ForeignKey('Job', related_name='job_history', on_delete=models.CASCADE, null=False)
    #: Time when this event occurred
    timestamp = models.DateTimeField('Date time', auto_now_add=True, help_text='History timestamp')
    #: Job Status for this event
    status = models.IntegerField('Job Status', help_text='History job status', null=True,
                                 choices=JobStatus.STATUS_LIST)
    #: Job event message
    message = models.TextField('History log', blank=True, null=True, help_text='History log')
    #: Event is only intended for Admin
    is_admin = models.BooleanField('Admin Message', default=False)

    def __str__(self):
        return '{}:{}:{}'.format(self.status, self.job, self.message) + ('(admin)' if self.is_admin else '')

    def __unicode__(self):
        return '{}:{}:{}'.format(self.status, self.job, self.message) + ('(admin)' if self.is_admin else '')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            super(JobHistory, self).save(force_insert, force_update, using, update_fields)
        except IntegrityError:
            pass


class JobAdminHistory(JobHistory):
    """A Job Event intended only for Admin use
    """

    class Meta:
        proxy = True

    objects = JobAdminHistoryManager()
