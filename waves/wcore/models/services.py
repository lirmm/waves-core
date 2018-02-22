"""
WAVES Services related models objects
"""
from __future__ import unicode_literals

import logging
import os
import collections
import swapper
from django.conf import settings
from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.db import transaction
from django.db.models import Q

from waves.wcore.adaptors.const import JobStatus
from waves.wcore.models.adaptors import AdaptorInitParam
from waves.wcore.models.runners import HasRunnerParamsMixin
from waves.wcore.models.base import TimeStamped, Described, ExportAbleMixin, Ordered, Slugged, ApiModel, WavesBaseModel
from waves.wcore.settings import waves_settings

__all__ = ['ServiceRunParam', 'ServiceManager', "SubmissionExitCode",
           'SubmissionOutput', 'SubmissionRunParam', 'BaseSubmission', 'BaseService']

logger = logging.getLogger(__name__)


class ServiceManager(models.Manager):
    """
    Service Model 'objects' Manager

    """

    def get_services(self, user=None):
        """
        Return services allowed for this specific user

        :param user: current User
        :return: services allowed for this user
        :rtype: Django queryset
        """
        if user is None:
            return self.none()

        if not user.is_anonymous():
            if user.is_superuser:
                queryset = self.all()
            elif user.is_staff:
                # Staff user have access their own Services and to all 'Test / Restricted / Public' made by others
                queryset = self.filter(
                    Q(status=self.model.SRV_DRAFT, created_by=user) |
                    Q(status__in=(self.model.SRV_TEST, self.model.SRV_RESTRICTED, self.model.SRV_REGISTERED,
                                  self.model.SRV_PUBLIC))
                )
            else:
                # Simply registered user have access only to "Public" and configured restricted access
                queryset = self.filter(
                    Q(status=self.model.SRV_RESTRICTED, restricted_client__in=(user,)) |
                    Q(status__in=(self.model.SRV_REGISTERED, self.model.SRV_PUBLIC))
                )
        # Non logged in user have only access to public services
        else:
            queryset = self.filter(status=self.model.SRV_PUBLIC)
        return queryset

    def get_by_natural_key(self, api_name, version, status):
        return self.get(api_name=api_name, version=version, status=status)


class ServiceRunParam(AdaptorInitParam):
    """ Defined runner param for Service model objects """

    class Meta:
        proxy = True


class BaseService(TimeStamped, Described, ApiModel, ExportAbleMixin, HasRunnerParamsMixin):
    class Meta:
        abstract = True
        ordering = ['name']
        verbose_name = 'Online Service'
        verbose_name_plural = "Online Services"
        unique_together = (('api_name', 'version', 'status'),)

    #: Service DRAFT status: online access granted only to creator
    SRV_DRAFT = 0
    #: Service TEST status: online access granted only to team members: creator + staff
    SRV_TEST = 1
    #: Service RESTRICTED status: online access granted only to specified users in list: creator + staff + specifics
    SRV_RESTRICTED = 2
    #: Service PUBLIC status: online access granted to anyone on front-end
    SRV_PUBLIC = 3
    #: Service REGISTERED status: online access granted to registered users only
    SRV_REGISTERED = 4
    #: Service status list for choices
    SRV_STATUS_LIST = [
        [SRV_DRAFT, 'Draft (only creator)'],
        [SRV_TEST, 'Staff (Team members)'],
        [SRV_REGISTERED, 'Registered'],
        [SRV_RESTRICTED, 'Restricted'],
        [SRV_PUBLIC, 'Public'],
    ]

    #: Dedicated Service object manager
    objects = ServiceManager()

    #: Service public name
    name = models.CharField('Service name', max_length=255, help_text='Service displayed name')
    #: Authors list, comma separated list
    authors = models.CharField('Authors', max_length=255, help_text="Tools authors", null=True)
    #: Citation link
    citations = models.CharField('Citation link', max_length=500, help_text="Citation link (Bibtex format)", null=True)
    #: Current service version (no history kept)
    version = models.CharField('Current version', max_length=10, null=True, blank=True, default='1.0',
                               help_text='Service displayed version')
    #: When status is 'RESTRICTED', set up user who have access to service
    restricted_client = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                               related_name='%(app_label)s_%(class)s_restricted_services',
                                               blank=True, verbose_name='Restricted clients',
                                               help_text='Public access is granted to everyone, '
                                                         'If status is \'Restricted\' you may restrict '
                                                         'access to specific users here.')
    #: Service current status (implied access granted to users)
    status = models.IntegerField(choices=SRV_STATUS_LIST, default=SRV_DRAFT,
                                 help_text='Service online status')
    #: Setup service's user notification
    email_on = models.BooleanField('Notify results', default=True,
                                   help_text='This service sends notification email')
    #: Set whether or not the service's outputs are knows in advance
    partial = models.BooleanField('Dynamic outputs', default=False,
                                  help_text='Set whether some service outputs are dynamic (not known in advance)')
    #: Service creator user
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    #: Service is identifier on computing platform with this id
    remote_service_id = models.CharField('Remote service tool ID', max_length=255, editable=False, null=True)
    #: List of related EDAM topics
    edam_topics = models.TextField('Edam topics', null=True, blank=True,
                                   help_text='Comma separated list of Edam ontology topics')
    #: List of related EDAM ontology operation
    edam_operations = models.TextField('Edam operations', null=True, blank=True,
                                       help_text='Comma separated list of Edam ontology operations')

    def clean(self):
        cleaned_data = super(BaseService, self).clean()
        return cleaned_data

    def __str__(self):
        """ String representation
        :return: str
        """
        return "{} v({})".format(self.name, self.version)

    def __unicode__(self):
        """ String representation
        :return: str
        """
        return "{} v({})".format(self.name, self.version)

    def set_defaults(self):
        super(BaseService, self).set_defaults()
        for sub in self.submissions.all():
            sub.set_defaults()

    @property
    def operations(self):
        """ List of specified EDAM operations related to this service
        :return: list
        """
        return self.edam_operations.split(',') if self.edam_operations else []

    @property
    def topics(self):
        """ List of specified EDAM topics related to this service

        :return: list
        """
        return self.edam_topics.split(',') if self.edam_topics else []

    @property
    def jobs(self):
        """ Return queryset for all service's related jobs

        :return: queryset
        """
        from waves.wcore.models import Job
        return Job.objects.filter(submission__in=self.submissions.all())

    @property
    def pending_jobs(self):
        """ Get current non-terminated service's related jobs

        :return: queryset
        """
        from waves.wcore.models import Job
        return Job.objects.filter(submission__in=self.submissions.all(),
                                  _status__in=JobStatus.PENDING_STATUS)

    @property
    def command(self):
        """ Return command parser for current service
        :return: BaseCommand """
        from waves.wcore.commands.command import BaseCommand
        return BaseCommand()

    @transaction.atomic
    def duplicate(self):
        """ Duplicate  a Service / with inputs / outputs / exit_code / runner params """
        from waves.wcore.api.v2.serializers import ServiceSerializer
        from django.contrib import messages
        serializer = ServiceSerializer()
        data = serializer.to_representation(self)
        srv = self.serializer(data=data)
        if srv.is_valid():
            srv.validated_data['name'] += ' (copy)'
            new_object = srv.save()
        else:
            messages.warning(message='Object could not be duplicated')
            new_object = self
        return new_object

    @property
    def sample_dir(self):
        """ Return sample dir for a service
        :return: str """
        return os.path.join(waves_settings.SAMPLE_DIR, self.api_name)

    @property
    def default_submission(self):
        """ Return Service default submission for web forms
        :return: First submission in list """
        try:
            return self.submissions.first()
        except ObjectDoesNotExist:
            return None

    @property
    def submissions_api(self):
        """ Returned submissions available on API """
        return self.submissions.filter(availability=1)

    def available_for_user(self, user):
        """ Access rules for submission form according to user
        :param user: Request User
        :return: boolean
        """
        # TODO reuse manager function or use authorization dedicated class
        # RULES to set if user can access service page
        # TODO reuse manager function or use authorization dedicated class
        if waves_settings.ALLOW_JOB_SUBMISSION is False or self.get_runner() is None:
            return False
        if self.status == self.SRV_PUBLIC or user.is_superuser():
            return True
        # RULES to set if user can access submissions
        return ((self.status == self.SRV_REGISTERED and not user.is_anonymous()) or
                (self.status == self.SRV_DRAFT and self.created_by == user) or
                (self.status == self.SRV_TEST and user.is_staff) or
                (self.status == self.SRV_RESTRICTED and (
                        user in self.restricted_client.all() or user.is_staff)))

    @property
    def serializer(self, context=None):
        from waves.wcore.import_export.services import ServiceSerializer
        return ServiceSerializer

    @property
    def importer(self):
        """ Short cut method to access runner importer (if any)"""
        return self.runner.importer

    def activate_deactivate(self):
        """ Published or unpublished Service """
        self.status = self.SRV_DRAFT if self.status is self.SRV_PUBLIC else self.SRV_PUBLIC
        self.save()

    @property
    def running_jobs(self):
        return self.jobs.filter(
            status__in=[JobStatus.JOB_CREATED, JobStatus.JOB_COMPLETED])

    def get_admin_url(self):
        return reverse('admin:{}_{}_change'.format(self._meta.app_label, self._meta.model_name), args=[self.pk])

    def get_admin_changelist(self):
        return reverse('admin:{}_{}_changelist'.format(self._meta.app_label, self._meta.model_name))


class Service(BaseService):
    """
    Represents a default swappable service on the platform
    """

    class Meta:
        swappable = swapper.swappable_setting('wcore', 'Service')


class BaseSubmission(TimeStamped, ApiModel, Ordered, Slugged, HasRunnerParamsMixin):
    class Meta:
        abstract = True
        unique_together = ('service', 'api_name')

    NOT_AVAILABLE = 0
    AVAILABLE_API = 1

    AVAILABILITY_CHOICES = (
        (NOT_AVAILABLE, "Disabled API"),
        (AVAILABLE_API, "Enabled API")
    )

    #: Related service model
    service = models.ForeignKey(swapper.get_model_name('wcore', 'Service'), on_delete=models.CASCADE, null=False,
                                related_name='submissions')
    #: Set whether this submission is available on REST API
    availability = models.IntegerField('Availability', default=AVAILABLE_API, choices=AVAILABILITY_CHOICES)
    #: Submission label
    name = models.CharField('Label', max_length=255, null=False, blank=False)

    def get_runner(self):
        """ Return the run configuration associated with this submission, or the default service one if not set
        :return: :class:`wcore.models.Runner`
        """
        if self.runner:
            return self.runner
        else:
            return self.service.runner

    @property
    def run_params(self):
        if not self.runner:
            return self.service.run_params
        return super(BaseSubmission, self).run_params

    def __str__(self):
        return '{}'.format(self.name)

    def __unicode__(self):
        return '{}'.format(self.name)

    @property
    def expected_inputs(self):
        """ Retrieve only expected inputs to submit a job """
        return self.inputs.filter(parent__isnull=True, required__isnull=False).order_by('order', '-required')

    def duplicate(self, service):
        """ Duplicate a submission with all its inputs """
        self.service = service
        init_inputs = self.inputs.all()
        self.pk = None
        self.save()
        for init_input in init_inputs:
            self.inputs.add(init_input.duplicate(self))
        # raise TypeError("Fake")
        return self

    @property
    def file_inputs(self):
        """ Only files inputs """
        from waves.wcore.models.inputs import FileInput
        return self.inputs.instance_of(FileInput).all()

    @property
    def params(self):
        """ Exclude files inputs """
        from waves.wcore.models.inputs import FileInput
        return self.inputs.not_instance_of(FileInput).all()

    @property
    def required_params(self):
        """ Return only required params """
        return self.inputs.filter(required=True)

    @property
    def submission_samples(self):
        from waves.wcore.models.inputs import FileInputSample
        return FileInputSample.objects.filter(file_input__submission=self)

    @property
    def pending_jobs(self):
        """ Get current Service Jobs """
        return self.service_jobs.filter(_status__in=JobStatus.PENDING_STATUS)

    def form_fields(self, data):
        form_fields = collections.OrderedDict({
            'title': forms.CharField(max_length=200),
            'email': forms.EmailField()
        })
        for in_param in self.expected_inputs.all().order_by('-required', 'order'):
            form_fields.update(in_param.form_widget(data=data.get(in_param.api_name, None)))
        return form_fields

    def get_admin_url(self):
        return reverse('admin:{}_{}_change'.format(self._meta.app_label, self._meta.model_name), args=[self.pk])

    def duplicate_api_name(self, api_name):
        """ Check is another entity is set with same api_name

        :param api_name:
        """
        return self.__class__.objects.filter(api_name=api_name, service=self.service).exclude(pk=self.pk)

    def available_for_user(self, user):
        """ Access rules for submission form according to user

        :param user: Request User
        :return: True or False
        """
        return self.service.available_for_user(user)


class Submission(BaseSubmission):
    class Meta:
        verbose_name = 'Submission method'
        verbose_name_plural = 'Submission methods'
        ordering = ('order',)
        swappable = swapper.swappable_setting('wcore', 'Submission')


class SubmissionOutput(TimeStamped, ApiModel):
    """ Represents usual submission expected output files
    """

    class Meta:
        verbose_name = 'Expected output'
        verbose_name_plural = 'Expected outputs'
        ordering = ['-created']

    #: Source field for api_name
    field_api_name = 'label'
    #: Displayed label
    label = models.CharField('Label', max_length=255, null=True, blank=False, help_text="Label")
    #: Output Name (internal)
    name = models.CharField('Name', max_length=255, null=True, blank=True, help_text="Output name")
    #: Related Submission
    submission = models.ForeignKey(swapper.get_model_name('wcore', 'Submission'), related_name='outputs',
                                   on_delete=models.CASCADE)
    #: Associated Submission Input if needed
    from_input = models.ForeignKey('AParam', null=True, blank=True, default=None, related_name='to_outputs',
                                   help_text='Is valuated from an input')
    #: Pattern to apply to associated input
    file_pattern = models.CharField('File name or name pattern', max_length=100, blank=False,
                                    help_text="Pattern is used to match input value (%s to retrieve value from input)")
    #: EDAM format
    edam_format = models.CharField('Edam format', max_length=255, null=True, blank=True,
                                   help_text="Edam ontology output format")
    #: EDAM data type
    edam_data = models.CharField('Edam data', max_length=255, null=True, blank=True,
                                 help_text="Edam ontology output data")
    #: Help text displayed on results
    help_text = models.TextField('Help Text', null=True, blank=True, )
    #: Expected file extension
    extension = models.CharField('File extension', max_length=15, blank=True, default="",
                                 help_text="Leave blank accept all, or set in file pattern")

    def __str__(self):
        """ String representation, return label """
        return "[{}] {}".format(self.label, self.name)

    def __unicode__(self):
        """ String representation, return label """
        return "[{}] {}".format(self.label, self.name)

    def clean(self):
        """ Check validity before saving """
        cleaned_data = super(SubmissionOutput, self).clean()
        if self.from_input and not self.file_pattern:
            raise ValidationError({'file_pattern': 'If valuated from input, you must set a file pattern'})
        return cleaned_data

    def save(self, *args, **kwargs):
        """ Override name with current label if not set"""
        if not self.name:
            self.name = self.label
        super(SubmissionOutput, self).save(*args, **kwargs)

    @property
    def ext(self):
        """ Return expected file output extension """
        file_name = None
        if self.name and '%s' in self.name and self.from_input and self.from_input.default:
            file_name = self.name % self.from_input.default
        elif self.name and '%s' not in self.name and self.name:
            file_name = self.name
        if '.' in file_name:
            return '.' + file_name.rsplit('.', 1)[1]
        else:
            return self.extension

    def duplicate_api_name(self, api_name):
        """ Check is another entity is set with same app_name """
        return SubmissionOutput.objects.filter(api_name=api_name, submission=self.submission).exclude(pk=self.pk)


class SubmissionExitCode(WavesBaseModel):
    """ Services Extended exit code, when non 0/1 usual ones """

    class Meta:
        verbose_name = 'Exit Code'
        unique_together = ('exit_code', 'submission')

    exit_code = models.IntegerField('Exit code value', default=0)
    message = models.CharField('Exit code message', max_length=255)
    submission = models.ForeignKey(swapper.get_model_name('wcore', 'Submission'),
                                   related_name='exit_codes',
                                   null=True,
                                   on_delete=models.CASCADE)
    is_error = models.BooleanField('Is an Error', default=False, blank=False)

    def __str__(self):
        return '{}:{}...'.format(self.exit_code, self.message[0:20])

    def __unicode__(self):
        return '{}:{}...'.format(self.exit_code, self.message[0:20])


class SubmissionRunParam(AdaptorInitParam):
    """ Defined runner param for Service model objects """

    class Meta:
        proxy = True
