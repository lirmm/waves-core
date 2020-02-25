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

import collections
import logging
import os

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db import transaction
from django.urls import reverse

from waves.core.const import JobStatus
from .runners import Runner
from .adaptors import AdaptorInitParam, HasAdaptorClazzMixin
from .base import TimeStamped, Described, ExportAbleMixin, Ordered, Slugged, ApiModel
from .managers import ServiceManager
from waves.settings import waves_settings

__all__ = ['ServiceRunParam', "SubmissionExitCode",
           'SubmissionOutput', 'SubmissionRunParam', 'Submission', 'Service']

logger = logging.getLogger(__name__)


class ServiceRunParam(AdaptorInitParam):
    """ Defined runner param for Service model objects """

    class Meta:
        proxy = True
        app_label = "waves"

    def get_value(self):
        if self.name == "command" and self.content_object is not None:
            if self.content_object.binary_file is not None:
                return self.content_object.binary_file.binary.path
        return super().get_value()


class HasRunnerParamsMixin(HasAdaptorClazzMixin):
    """ Model mixin to manage params overriding and shortcut method to retrieve concrete classes """

    class Meta:
        abstract = True

    _runner = None
    runner = models.ForeignKey(Runner,
                               verbose_name="Computing infrastructure",
                               related_name='%(app_label)s_%(class)s_runs',
                               null=True,
                               db_column='runner_id',
                               on_delete=models.SET_NULL,
                               help_text='Service job runs configuration')

    @classmethod
    def from_db(cls, db, field_names, values):
        """ Executed each time a Service is restored from DB layer"""
        instance = super(HasRunnerParamsMixin, cls).from_db(db, field_names, values)
        # instance._runner = instance.get_runner()
        return instance

    @property
    def config_changed(self):
        return self._runner != self.runner

    @property
    def run_params(self):
        """
        Return a list of tuples representing current service adapter init params

        :return: a Dictionary (param_name=param_service_value or runner_param_default if not set
        :rtype: dict
        """
        # Retrieve the ones defined in DB
        object_params = super(HasRunnerParamsMixin, self).run_params
        # Retrieve the ones defined for runner
        runners_params = self.get_runner().run_params
        # Merge params from runner (defaults and/or not override-able)
        runners_params.update(object_params)
        return runners_params

    @property
    def adaptor_defaults(self):
        """ Retrieve init params defined associated concrete class (from runner attribute) """
        return self.get_runner().run_params if self.get_runner() else {}

    def get_runner(self):
        """ Return effective runner (could be overridden is any subclasses) """
        return self.runner

    @property
    def clazz(self):
        return self.get_runner().clazz

    @clazz.setter
    def clazz(self, clazz):
        # fake setter since the actual clazz is defined in runner
        pass


class Service(TimeStamped, Described, ApiModel, ExportAbleMixin,
              HasRunnerParamsMixin):
    class Meta:
        db_table = 'wcore_service'
        ordering = ['name']
        verbose_name = 'Waves Service'
        verbose_name_plural = "Waves Services"
        unique_together = (('api_name', 'version', 'status'), ('api_name', 'version'))
        app_label = "waves"

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
    #: Service binary executable
    binary_file = models.ForeignKey('ServiceBinaryFile', null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text="If set, 'Execution parameter' param line:'command' will be ignored")

    def clean(self):
        cleaned_data = super(Service, self).clean()
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
        """Set runs params with defaults issued from adapter class object """
        if self.runner is not None:
            self.adaptor_params.all().delete()
            object_type = ContentType.objects.get_for_model(self)
            # Reset all old values
            for runner_param in self.runner.adaptor_params.filter(prevent_override=False):
                ServiceRunParam.objects.create(name=runner_param.name,
                                               value=runner_param.value,
                                               crypt=(runner_param.name == 'password'),
                                               prevent_override=False,
                                               content_type=object_type,
                                               object_id=self.pk)

        for sub in self.submissions.all():
            sub.adaptor_params.all().delete()
            object_type = ContentType.objects.get_for_model(sub)
            for runner_param in sub.get_runner().adaptor_params.filter(prevent_override=False):
                SubmissionRunParam.objects.create(name=runner_param.name,
                                                  value=runner_param.value,
                                                  crypt=(runner_param.name == 'password'),
                                                  prevent_override=False,
                                                  content_type=object_type,
                                                  object_id=self.pk)

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
        from waves.models import Job
        return Job.objects.filter(submission__in=self.submissions.all())

    @property
    def pending_jobs(self):
        """ Get current non-terminated service's related jobs

        :return: queryset
        """
        from waves.models import Job
        return Job.objects.filter(submission__in=self.submissions.all(),
                                  _status__in=JobStatus.PENDING_STATUS)

    @property
    def command_parser(self):
        """ Return command parser for current service
        TODO: add related BaseCommand from waves_settings (same as Adaptor class loading)
        :return: BaseCommand """
        from waves import BaseCommand
        return BaseCommand()

    @transaction.atomic
    def duplicate(self):
        """ Duplicate  a Service / with inputs / outputs / exit_code / runner params """
        from waves.api.current import serializers
        serializer = serializers.ServiceSerializer()
        data = serializer.to_representation(self)
        srv = self.serializer(data=data)
        if srv.is_valid():
            srv.validated_data['name'] += ' (copy)'
            new_object = srv.save()
        else:
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
        return self.submissions.filter(availability=Submission.AVAILABLE_API)

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
        if self.status == self.SRV_PUBLIC or user.is_superuser:
            return True
        # RULES to set if user can access submissions
        return ((self.status == self.SRV_REGISTERED and not user.is_anonymous) or
                (self.status == self.SRV_DRAFT and self.created_by == user) or
                (self.status == self.SRV_TEST and user.is_staff) or
                (self.status == self.SRV_RESTRICTED and (
                        user in self.restricted_client.all() or user.is_staff)))

    @property
    def serializer(self, context=None):
        from waves.core.import_export import ServiceSerializer
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


class Submission(TimeStamped, ApiModel, Ordered, Slugged, HasRunnerParamsMixin):
    class Meta:
        db_table = 'wcore_submission'
        verbose_name = 'Submission method'
        verbose_name_plural = 'Submission methods'
        ordering = ('order',)
        unique_together = ('service', 'api_name')
        app_label = "waves"

    NOT_AVAILABLE = 0
    AVAILABLE_API = 1

    AVAILABILITY_CHOICES = (
        (NOT_AVAILABLE, "Disabled API"),
        (AVAILABLE_API, "Enabled API")
    )

    #: Related service model
    service = models.ForeignKey('Service', on_delete=models.CASCADE, null=False,
                                related_name='submissions')
    #: Set whether this submission is available on REST API
    availability = models.IntegerField('Availability', default=AVAILABLE_API, choices=AVAILABILITY_CHOICES)
    #: Submission label
    name = models.CharField('Label', max_length=255, null=False, blank=False)

    def get_runner(self):
        """ Return the run configuration associated with this submission, or the default service one if not set
        :return: :class:`core.models.Runner`
        """
        if self.runner:
            return self.runner
        else:
            return self.service.runner

    @property
    def run_params(self):
        if not self.runner:
            return self.service.run_params
        return super(Submission, self).run_params

    @property
    def command_parser(self):
        """ Recipient for future dedicated command parser for specific submission
        TODO: manage command_parser such as mocks
        """
        return self.service.command_parser

    def __str__(self):
        return '{}'.format(self.name)

    def __unicode__(self):
        return '{}'.format(self.name)

    @property
    def expected_inputs(self):
        """ Retrieve only expected inputs to submit a job """
        return self.inputs.filter(parent__isnull=True, required__isnull=False).order_by('order', '-required')

    @property
    def root_inputs(self):
        """ Retrieve only expected inputs to submit a job """
        return self.inputs.filter(parent__isnull=True).order_by('order', '-required')

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
        from waves.models import FileInput
        return self.inputs.instance_of(FileInput).all()

    @property
    def params(self):
        """ Exclude files inputs """
        from waves.models import FileInput
        return self.inputs.not_instance_of(FileInput).all()

    @property
    def required_params(self):
        """ Return only required params """
        return self.inputs.filter(required=True)

    @property
    def submission_samples(self):
        from waves.models import FileInputSample
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


class SubmissionOutput(TimeStamped, ApiModel):
    """ Represents usual submission expected output files
    """

    class Meta:
        db_table = 'wcore_submissionoutput'
        verbose_name = 'Expected output'
        verbose_name_plural = 'Expected outputs'
        ordering = ['-created']
        app_label = "waves"

    #: Source field for api_name
    field_api_name = 'label'
    #: Displayed label
    label = models.CharField('Label', max_length=255, null=True, blank=False, help_text="Label")
    #: Output Name (internal)
    name = models.CharField('Name', max_length=255, null=True, blank=True, help_text="Output name")
    #: Related Submission
    submission = models.ForeignKey('Submission', related_name='outputs',
                                   on_delete=models.CASCADE)
    #: Associated Submission Input if needed
    from_input = models.ForeignKey('AParam', null=True, blank=True, default=None, related_name='to_outputs',
                                   help_text='Is valuated from an input', on_delete=models.CASCADE)
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
    extension = models.CharField('File extension (internal)', max_length=15, blank=True, default="",
                                 help_text="Used on WEB for display/download ")

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

    def duplicate_api_name(self, api_name):
        """ Check is another entity is set with same app_name """
        return SubmissionOutput.objects.filter(api_name=api_name, submission=self.submission).exclude(pk=self.pk)


class SubmissionExitCode(models.Model):
    """ Services Extended exit code, when non 0/1 usual ones """

    class Meta:
        db_table = 'wcore_submissionexitcode'
        verbose_name = 'Exit Code'
        unique_together = ('exit_code', 'submission')
        app_label = "waves"

    exit_code = models.IntegerField('Exit code value', default=0)
    message = models.CharField('Exit code message', max_length=255)
    submission = models.ForeignKey('Submission',
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
        app_label = "waves"
