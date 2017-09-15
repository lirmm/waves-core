"""
WAVES Services related models objects
"""
from __future__ import unicode_literals

import logging
import os

import swapper
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError, MultipleObjectsReturned
from django.core.urlresolvers import reverse
from django.db import models
from django.db import transaction
from django.db.models import Q

import waves.wcore.adaptors.const
from waves.wcore.models.adaptors import *
from waves.wcore.models.base import *
from waves.wcore.models.runners import Runner
from waves.wcore.settings import waves_settings

__all__ = ['ServiceRunParam', 'ServiceManager', 'BaseService', 'Submission', "SubmissionExitCode",
           'SubmissionOutput', 'SubmissionRunParam', 'HasRunnerParamsMixin']

logger = logging.getLogger(__name__)


class ServiceManager(models.Manager):
    """
    Service Model 'objects' Manager
    """

    def get_services(self, user=None, for_api=False):
        """

        :param user: current User
        :param for_api: filter only wapi:api_v2 enabled, either return only web enabled
        :return: QuerySet for services
        :rtype: QuerySet
        """
        if user is not None and not user.is_anonymous():
            if user.is_superuser:
                queryset = self.all()
            elif user.is_staff:
                # Staff user have access their own Services and to all 'Test / Restricted / Public' made by others
                queryset = self.filter(
                    Q(status=self.model.SRV_DRAFT, created_by=user) |
                    Q(status__in=(self.model.SRV_TEST, self.model.SRV_RESTRICTED,
                                  self.model.SRV_PUBLIC))
                )
            else:
                # Simply registered user have access only to "Public" and configured restricted access
                queryset = self.filter(
                    Q(status=self.model.SRV_RESTRICTED, restricted_client__in=(user,)) |
                    Q(status=self.model.SRV_PUBLIC)
                )
        # Non logged in user have only access to public services
        else:
            queryset = self.filter(status=self.model.SRV_PUBLIC)
        if for_api:
            queryset = queryset.filter(api_on=True)
        else:
            queryset = queryset.filter(web_on=True)
        return queryset

    def get_api_services(self, user=None):
        """ Return all wapi:api_v2 enabled service to User
        """
        return self.get_services(user, for_api=True)

    def get_web_services(self, user=None):
        """ Return all web enabled services """
        return self.get_services(user)

    def get_by_natural_key(self, api_name, version, status):
        return self.get(api_name=api_name, version=version, status=status)


class ServiceRunParam(AdaptorInitParam):
    """ Defined runner param for Service model objects """

    class Meta:
        proxy = True


class HasRunnerParamsMixin(HasAdaptorClazzMixin):
    """ Model mixin to manage params overriding and shortcut method to retrieve concrete classes """

    class Meta:
        abstract = True

    _runner = None
    runner = models.ForeignKey(Runner, related_name='%(app_label)s_%(class)s_runs', null=True, blank=False,
                               on_delete=models.SET_NULL,
                               help_text='Service job runs adapter')

    @classmethod
    def from_db(cls, db, field_names, values):
        """ Executed each time a Service is restored from DB layer"""
        instance = super(HasRunnerParamsMixin, cls).from_db(db, field_names, values)
        instance._runner = instance.runner
        return instance

    def set_run_params_defaults(self):
        """ Set runs params with defaults issued from concrete class object """
        if self.runner:
            if self.adaptor_params.count() > 0:
                self.adaptor_params.all().delete()
            runners_defaults = self.runner.run_params
            current_defaults = self.run_params
            [runners_defaults.pop(k, None) for k in current_defaults if k == 'protocol']
            queryset = self.runner.adaptor_params.filter(name__in=runners_defaults.keys()) \
                if runners_defaults else self.runner.adaptor_params.all()
            queryset = queryset.exclude(prevent_override=True)
            for runner_param in queryset:
                if runner_param.prevent_override:
                    try:
                        self.adaptor_params.get(name=runner_param.name).delete()
                    except ObjectDoesNotExist:
                        continue
                    except MultipleObjectsReturned:
                        self.adaptor_params.filter(name=runner_param.name).delete()
                else:
                    defaults = {'value': runner_param.value, 'prevent_override': runner_param.prevent_override,
                                'crypt': runner_param.crypt}
                    object_ctype = ContentType.objects.get_for_model(self)
                    obj, created = AdaptorInitParam.objects.update_or_create(defaults=defaults,
                                                                             content_type=object_ctype,
                                                                             object_id=self.pk, name=runner_param.name)
                    logger.debug('Object %s, %s', obj, created)

    @property
    def clazz(self):
        return self.get_runner().clazz if self.get_runner() else None

    @property
    def config_changed(self):
        return self._runner != self.runner

    @property
    def run_params(self):
        """
        Return a list of tuples representing current service adaptor init params
        :return: a Dictionary (param_name=param_service_value or runner_param_default if not set
        :rtype: dict
        """
        object_params = super(HasRunnerParamsMixin, self).run_params
        runners_default = self.get_runner().run_params
        runners_default.update(object_params)
        return runners_default

    @property
    def adaptor_defaults(self):
        """ Retrieve init params defined associated concrete class (from runner attribute) """
        return self.get_runner().run_params if self.get_runner() else {}

    def get_runner(self):
        """ Return effective runner (could be overridden is any subclasses) """
        return self.runner


class BaseService(TimeStamped, Described, ApiModel, ExportAbleMixin, HasRunnerParamsMixin):
    class Meta:
        abstract = True

    SRV_DRAFT = 0
    SRV_TEST = 1
    SRV_RESTRICTED = 2
    SRV_PUBLIC = 3
    SRV_STATUS_LIST = [
        [SRV_DRAFT, 'Draft'],
        [SRV_TEST, 'Test'],
        [SRV_RESTRICTED, 'Restricted'],
        [SRV_PUBLIC, 'Public'],
    ]

    # manager
    objects = ServiceManager()
    # fields
    name = models.CharField('Service name', max_length=255, help_text='Service displayed name')
    version = models.CharField('Current version', max_length=10, null=True, blank=True, default='1.0',
                               help_text='Service displayed version')
    restricted_client = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                               related_name='%(app_label)s_%(class)s_restricted_services',
                                               blank=True, verbose_name='Restricted clients',
                                               help_text='By default access is granted to everyone, '
                                                         'you may restrict access here.')
    status = models.IntegerField(choices=SRV_STATUS_LIST, default=SRV_DRAFT,
                                 help_text='Service online status')
    api_on = models.BooleanField('Available on API', default=True,
                                 help_text='Service is available for wapi:api_v2 calls')
    web_on = models.BooleanField('Available on WEB', default=True, help_text='Service is available for web front')
    email_on = models.BooleanField('Notify results', default=True,
                                   help_text='This service sends notification email')
    partial = models.BooleanField('Dynamic outputs', default=False,
                                  help_text='Set whether some service outputs are dynamic (not known in advance)')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    remote_service_id = models.CharField('Remote service tool ID', max_length=255, editable=False, null=True)
    edam_topics = models.TextField('Edam topics', null=True, blank=True,
                                   help_text='Comma separated list of Edam ontology topics')
    edam_operations = models.TextField('Edam operations', null=True, blank=True,
                                       help_text='Comma separated list of Edam ontology operations')

    def clean(self):
        cleaned_data = super(BaseService, self).clean()
        # TODO check changed status with at least one submission available on each submission channel (web/wapi:api_v2)
        return cleaned_data

    def __str__(self):
        return "%s v(%s)" % (self.name, self.version)

    def set_run_params_defaults(self):
        super(BaseService, self).set_run_params_defaults()
        for sub in self.submissions.all():
            sub.set_run_params_defaults()

    @property
    def jobs(self):
        """ Get current Service Jobs """
        from waves.wcore.models import Job
        return Job.objects.filter(submission__in=self.submissions.all())

    @property
    def pending_jobs(self):
        """ Get current Service Jobs """
        from waves.wcore.models import Job
        return Job.objects.filter(submission__in=self.submissions.all(),
                                  _status__in=waves.wcore.adaptors.const.PENDING_STATUS)

    def import_service_params(self):
        """ Try to import service param configuration issued from adaptor

        :return: None
        """
        if not self.runner:
            raise ImportError(u'Unable to import if no adaptor is set')

    @property
    def command(self):
        """ Return command parser for current Service """
        from waves.wcore.commands.command import BaseCommand
        return BaseCommand()

    def service_submission_inputs(self, submission=None):
        """
        Retrieve all
        :param submission:
        :return: corresponding QuerySet object
        :rtype: QuerySet
        """
        if not submission:
            return self.default_submission.inputs
        return submission.inputs

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
        """ Return expected sample dir for a Service """
        return os.path.join(waves_settings.SAMPLE_DIR, self.api_name)

    @property
    def default_submission(self):
        """ Return Service default submission for web forms """
        try:
            return self.submissions.filter(availability__in=(1, 3)).first()
        except ObjectDoesNotExist:
            return None

    @property
    def default_submission_api(self):
        """ Return Service default submission for wapi:api_v2 """
        try:
            return self.submissions.filter(availability__gt=2).first()
        except ObjectDoesNotExist:
            return None

    @property
    def submissions_web(self):
        """ Returned submissions available on WEB forms """
        return self.submissions.filter(availability__in=(1, 3))

    @property
    def submissions_api(self):
        """ Returned submissions available on API """
        return self.submissions.filter(availability__gt=2)

    def available_for_user(self, user):
        """ Access rules for submission form according to user
        :param user: Request User
        :return: True or False
        """
        if user.is_anonymous():
            return (self.runner is not None and self.status == self.SRV_PUBLIC and
                    waves_settings.ALLOW_JOB_SUBMISSION is True)
        # RULES to set if user can access submissions
        return self.runner is not None and (self.runner is not None and self.status == self.SRV_PUBLIC and
                                            waves_settings.ALLOW_JOB_SUBMISSION is True) or \
               (self.status == self.SRV_DRAFT and self.created_by == user) or \
               (self.status == self.SRV_TEST and user.is_staff) or \
               (self.status == self.SRV_RESTRICTED and (
                   user in self.restricted_client.all() or user.is_staff)) or \
               user.is_superuser

    @property
    def serializer(self, context=None):
        from waves.wcore.models.serializers.services import ServiceSerializer
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
            status__in=[waves.wcore.adaptors.const.JOB_CREATED, waves.wcore.adaptors.const.JOB_COMPLETED])

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=[self.pk])

    def get_admin_changelist(self):
        return reverse('admin:%s_%s_changelist' % (self._meta.app_label, self._meta.model_name))


class Service(BaseService):
    """
    Represents a default swappable service on the platform
    """

    class Meta:
        ordering = ['name']
        verbose_name = 'Online Service'
        verbose_name_plural = "Online Services"
        unique_together = (('api_name', 'version', 'status'),)
        swappable = swapper.swappable_setting('wcore', 'Service')


class BaseSubmission(TimeStamped, ApiModel, Ordered, Slugged, HasRunnerParamsMixin):
    class Meta:
        abstract = True

    NOT_AVAILABLE = 0
    AVAILABLE_WEB_ONLY = 1
    AVAILABLE_API_ONLY = 2
    AVAILABLE_BOTH = 3
    service = models.ForeignKey(swapper.get_model_name('wcore', 'Service'), on_delete=models.CASCADE, null=False,
                                related_name='submissions')
    availability = models.IntegerField('Availability', default=3,
                                       choices=((NOT_AVAILABLE, "Not Available"),
                                                (AVAILABLE_WEB_ONLY, "Available web only"),
                                                (AVAILABLE_API_ONLY, "Available api only"),
                                                (AVAILABLE_BOTH, "Available api and web")))
    name = models.CharField('Form title', max_length=255, null=False, blank=False)

    @property
    def config_changed(self):
        return self.runner != self.get_runner() or self._runner != self.runner

    def set_run_params_defaults(self):
        if self.config_changed and self._runner:
            self.adaptor_params.all().delete()
        super(BaseSubmission, self).set_run_params_defaults()

    @property
    def run_params(self):
        if not self.runner:
            return self.service.run_params
        elif self.runner.pk == self.service.runner.pk:
            # same runner but still overriden in bo, so merge params (submission params prevents)
            service_run_params = self.service.run_params
            object_run_params = super(BaseSubmission, self).run_params
            service_run_params.update(object_run_params)
            return service_run_params
        return super(BaseSubmission, self).run_params

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
        """ return whether submission is available for wapi:api_v2 calls """
        return self.availability >= 2

    def __str__(self):
        return '[%s]' % self.name

    @property
    def expected_inputs(self):
        """ Retrieve only expected inputs to submit a job """
        return self.inputs.filter(parent__isnull=True, required__isnull=False)

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
        return self.service_jobs.filter(status__in=waves.wcore.adaptors.const.PENDING_STATUS)

    def duplicate_api_name(self):
        """ Check is another entity is set with same api_name """
        return BaseSubmission.objects.filter(api_name__startswith=self.api_name, service=self.service)


class Submission(BaseSubmission):
    class Meta:
        verbose_name = 'Submission form'
        verbose_name_plural = 'Submission forms'
        ordering = ('order',)
        unique_together = ('service', 'api_name')
        swappable = swapper.swappable_setting('wcore', 'Submission')


class SubmissionOutput(TimeStamped, ApiModel):
    """
    Represents usual service expected output files
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
    name = models.CharField('Name', max_length=255, null=True, blank=True, help_text="Label")
    #: Related Submission
    submission = models.ForeignKey(Submission, related_name='outputs', on_delete=models.CASCADE)
    #: Associated Submission Input if needed
    from_input = models.ForeignKey('AParam', null=True, blank=True, default=None, related_name='to_outputs',
                                   help_text='Is valuated from an input')
    #: Pattern to apply to associated input
    file_pattern = models.CharField('File name or name pattern', max_length=100, blank=False,
                                    help_text="Pattern is used to match input value (%s to retrieve value from input)")
    #: EDAM format
    edam_format = models.CharField('Edam format', max_length=255, null=True, blank=True,
                                   help_text="Edam ontology format")
    #: EDAM data type
    edam_data = models.CharField('Edam data', max_length=255, null=True, blank=True,
                                 help_text="Edam ontology data")
    #: Help text displayed on results
    help_text = models.TextField('Help Text', null=True, blank=True, )
    #: File extension
    extension = models.CharField('Extension', max_length=5, blank=True, default="",
                                 help_text="Leave blank for *, or set in file pattern")

    def __str__(self):
        return self.label

    def clean(self):
        cleaned_data = super(SubmissionOutput, self).clean()
        if self.from_input and not self.file_pattern:
            raise ValidationError({'file_pattern': 'If valuated from input, you must set a file pattern'})
        return cleaned_data

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.label
        super(SubmissionOutput, self).save(*args, **kwargs)

    @property
    def ext(self):
        """
        return expected file output extension
        """
        file_name = None
        if self.name and '%s' in self.name and self.from_input and self.from_input.default:
            file_name = self.name % self.from_input.default
        elif self.name and '%s' not in self.name and self.name:
            file_name = self.name
        if '.' in file_name:
            return '.' + file_name.rsplit('.', 1)[1]
        else:
            return self.extension


class SubmissionExitCode(WavesBaseModel):
    """ Services Extended exit code, when non 0/1 usual ones"""

    class Meta:
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
