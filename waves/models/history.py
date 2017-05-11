from django.db import models

from waves.models.jobs import Job


class JobHistoryManager(models.Manager):
    def create(self, **kwargs):
        """ Force 'is_admin' flag for JobAdminHistory models objects
        :return: a JobAdminHistory object
        """
        if 'message' not in kwargs:
            kwargs['message'] = kwargs.get('job').message
        return super(JobHistoryManager, self).create(**kwargs)


class JobAdminHistoryManager(JobHistoryManager):
    def get_queryset(self):
        """
        Specific query set to filter only :class:`waves.models.jobs.JobAdminHistory` objects
        :return: QuerySet
        """
        return super(JobAdminHistoryManager, self).get_queryset().filter(is_admin=True)

    def create(self, **kwargs):
        """ Force 'is_admin' flag for JobAdminHistory models objects
        :return: a JobAdminHistory object
        """
        kwargs.update({'is_admin': True})
        return super(JobAdminHistoryManager, self).create(**kwargs)


class JobHistory(models.Model):
    """ Represents a job status history event
    """

    class Meta:
        db_table = 'waves_job_history'
        ordering = ['-timestamp', '-status']
        unique_together = ('job', 'timestamp', 'status', 'is_admin')

    objects = JobHistoryManager()
    #: Related :class:`waves.models.jobs.Job`
    job = models.ForeignKey('Job', related_name='job_history', on_delete=models.CASCADE, null=False)
    #: Time when this event occurred
    timestamp = models.DateTimeField('Date time', auto_now_add=True, help_text='History timestamp')
    #: Job Status for this event
    status = models.IntegerField('Job Status', help_text='History job status', null=True, choices=Job.STATUS_LIST)
    #: Job event message
    message = models.TextField('History log', blank=True, null=True, help_text='History log')
    #: Event is only intended for Admin
    is_admin = models.BooleanField('Admin Message', default=False)

    def __str__(self):
        return '%s:%s:%s' % (self.status, self.job, self.message) + ('(admin)' if self.is_admin else '')


class JobAdminHistory(JobHistory):
    """A Job Event intended only for Admin use
    """

    class Meta:
        proxy = True

    objects = JobAdminHistoryManager()
