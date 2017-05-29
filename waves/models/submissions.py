""" Each WAVES service allows multiple job 'submissions' """
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models

from waves.models import TimeStamped, ApiModel, Ordered, Slugged, Service
from waves.models.adaptors import AdaptorInitParam, HasRunnerParamsMixin

__all__ = ['Submission', 'SubmissionOutput', 'SubmissionExitCode', 'SubmissionRunParam']


class SubmissionManager(models.Manager):
    pass


class Submission(TimeStamped, ApiModel, Ordered, Slugged, HasRunnerParamsMixin):
    """ Represents a service submission parameter set for a service """

    class Meta:
        db_table = 'waves_submission'
        verbose_name = 'Submission'
        verbose_name_plural = 'Submissions'
        unique_together = ('service', 'api_name')
        ordering = ('order',)

    availability = models.IntegerField('Availability', default=3,
                                       choices=[(0, "Not Available"),
                                                (1, "Available on web only"),
                                                (2, "Available on waves:api_v2 only"),
                                                (3, "Available on both")])
    name = models.CharField('Submission title', max_length=255, null=False, blank=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=False, related_name='submissions')

    @property
    def config_changed(self):
        return self.runner != self.get_runner() or self._runner != self.runner

    def set_run_params_defaults(self):
        if self.config_changed and self._runner:
            self.adaptor_params.all().delete()
        super(Submission, self).set_run_params_defaults()

    @property
    def run_params(self):
        if not self.runner:
            return self.service.run_params
        elif self.runner.pk == self.service.runner.pk:
            # same runner but still overriden in bo, so merge params (submission params prevents)
            service_run_params = self.service.run_params
            object_run_params = super(Submission, self).run_params
            service_run_params.update(object_run_params)
            return service_run_params
        return super(Submission, self).run_params

    def get_runner(self):
        if self.runner:
            return self.runner
        else:
            return self.service.runner

    @property
    def available_online(self):
        """ return whether submission is available online """
        return self.availability == 1 or self.availability == 3

    @property
    def available_api(self):
        """ return whether submission is available for waves:api_v2 calls """
        return self.availability >= 2

    def __str__(self):
        return '[%s]' % self.name

    @property
    def expected_inputs(self):
        """ Retrieve only expected inputs to submit a job """
        return self.submission_inputs.filter(parent__isnull=True).exclude(required=None)

    def duplicate(self, service):
        """ Duplicate a submission with all its inputs """
        self.service = service
        init_inputs = self.submission_inputs.all()
        self.pk = None
        self.save()
        for init_input in init_inputs:
            self.submission_inputs.add(init_input.duplicate(self))
        # raise TypeError("Fake")
        return self

    @property
    def file_inputs(self):
        """ Only files inputs """
        from waves.models.inputs import FileInput
        return self.submission_inputs.instance_of(FileInput).all()

    @property
    def params(self):
        """ Exclude files inputs """
        from waves.models.inputs import FileInput
        return self.submission_inputs.not_instance_of(FileInput).all()

    @property
    def required_params(self):
        """ Return only required params """
        return self.submission_inputs.filter(required=True)

    @property
    def submission_samples(self):
        from waves.models.samples import FileInputSample
        return FileInputSample.objects.filter(file_input__submission=self)

    @property
    def pending_jobs(self):
        """ Get current Service Jobs """
        from waves.models import Job
        return self.service_jobs.filter(status__in=Job.PENDING_STATUS)

    def duplicate_api_name(self):
        """ Check is another entity is set with same api_name """
        return Submission.objects.filter(api_name__startswith=self.api_name, service=self.service)


class SubmissionOutput(TimeStamped, ApiModel):
    """
    Represents usual service parameters output values (share same attributes with ServiceParameters)
    """

    class Meta:
        db_table = 'waves_submission_output'
        verbose_name = 'Output'
        verbose_name_plural = 'Outputs'
        ordering = ['-created']

    field_api_name = 'label'
    label = models.CharField('Label', max_length=255, null=True, blank=False, help_text="Label")
    submission = models.ForeignKey(Submission, related_name='outputs', on_delete=models.CASCADE)
    from_input = models.ForeignKey('AParam', null=True, blank=True, related_name='to_outputs',
                                   help_text='Valuated with input')
    file_pattern = models.CharField('File name or name pattern', max_length=100, blank=False,
                                    help_text="Pattern is used to match input value (%s to retrieve value from input)")
    edam_format = models.CharField('Edam format', max_length=255, null=True, blank=True, help_text="Edam format")
    edam_data = models.CharField('Edam data', max_length=255, null=True, blank=True, help_text="Edam data")
    help_text = models.TextField('Help Text', null=True, blank=True, )

    def __str__(self):
        return '%s (%s)' % (self.label, self.ext)

    def clean(self):
        cleaned_data = super(SubmissionOutput, self).clean()
        if self.from_input and not self.file_pattern:
            raise ValidationError({'file_pattern': 'If valuated from input, you must set a file pattern'})
        if not self.from_input and not self.name:
            raise ValidationError({'name': 'If not valuated from input, you must set a file name'})
        return cleaned_data

    def save(self, *args, **kwargs):
        super(SubmissionOutput, self).save(*args, **kwargs)

    @property
    def name(self):
        return self.file_pattern

    @property
    def ext(self):
        """ return expected file output extension """
        file_name = "fake.txt"
        if '%s' in self.name and self.from_input.default:
            file_name = self.name % self.from_input.default
        elif '%s' not in self.name and self.name:
            file_name = self.name
        if '.' in file_name:
            return '.' + file_name.rsplit('.', 1)[1]
        else:
            return '.txt'


class SubmissionExitCode(models.Model):
    """ Services Extended exit code, when non 0/1 usual ones"""

    class Meta:
        db_table = 'waves_service_exitcode'
        verbose_name = 'Exit Code'
        unique_together = ('exit_code', 'submission')

    exit_code = models.IntegerField('Exit code value')
    message = models.CharField('Exit code message', max_length=255)
    submission = models.ForeignKey(Submission, related_name='exit_codes', on_delete=models.CASCADE)
    is_error = models.BooleanField('Is an Error', default=False, blank=False)

    def __str__(self):
        return '{}:{}...'.format(self.exit_code, self.message[0:20])


class SubmissionRunParam(AdaptorInitParam):
    """ Defined runner param for Service model objects """

    class Meta:
        proxy = True
