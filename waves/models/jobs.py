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

import json
import logging
import os
import shutil
from os.path import join

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import smart_text
from django.utils.html import format_html

from waves.core.const import OptType, ParamType, JobStatus, JobRunDetails
from waves.core.exceptions import AdaptorException, JobInconsistentStateError, WavesException
from waves.core.utils import LoggerClass, allow_display_online
from waves.settings import waves_settings
from .base import TimeStamped, Slugged, Ordered, UrlMixin, ApiModel
from .managers import JobManager, JobInputManager, JobOutputManager

logger = logging.getLogger(__name__)

__all__ = ['Job', 'JobInput', 'JobOutput']


class Job(TimeStamped, Slugged, UrlMixin, LoggerClass):
    """
    A job represent a request for executing a service, it requires values from specified required input from related
    service
    """
    # non persistent field, used for history savings see signals
    #: Current message associated with job object, not directly stored in job table, but in history
    message = None
    #: Job run details retrieved or not
    _run_details = None

    class Meta(TimeStamped.Meta):
        verbose_name = 'Job'
        verbose_name_plural = "Jobs"
        ordering = ['-updated', '-created']
        db_table = 'wcore_job'
        app_label = "waves"

    objects = JobManager()
    #: Job Title, automatic or set by user upon submission
    title = models.CharField('Job title', max_length=255, null=True, blank=True)
    #: Job related Service
    submission = models.ForeignKey('Submission', related_name='service_jobs',
                                   null=True, on_delete=models.SET_NULL)
    #: Job status issued from last retrieve on DB
    _status = models.IntegerField('Job status', choices=JobStatus.STATUS_LIST,
                                  default=JobStatus.JOB_CREATED)
    #: Job last status for which we sent a notification email
    status_mail = models.IntegerField(editable=False, default=9999)
    #: Job associated client, may be null for anonymous submission
    client = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE,
                               related_name='clients_job', help_text='Associated registered user')
    #: Email to notify job status to
    email_to = models.EmailField('Email results', null=True, blank=True, help_text='Notify results to this email')
    #: Job ExitCode (mainly for admin purpose)
    exit_code = models.IntegerField('Job system exit code', default=0, help_text="Job exit code on relative adapter")
    #: Tell whether job results files are available for download from client
    results_available = models.BooleanField('Results are available', default=False, editable=False)
    #: Job last status retry count (max before Error set in conf)
    nb_retry = models.IntegerField('Nb Retry', editable=False, default=0)
    #: Jobs are remotely executed, store the adapter job identifier
    remote_job_id = models.CharField('Remote job ID', max_length=255, editable=False, null=True)
    #: Jobs sometime can gain access to a remote history, store the adapter history identifier
    remote_history_id = models.CharField('Remote history ID', max_length=255, editable=False, null=True)
    #: Final generated command line
    _command_line = models.CharField('Final generated command line', max_length=255, editable=False, null=True)
    #: adaptor serialized values
    _adaptor = models.TextField('Adapter classed used for this Job', editable=False, null=True)
    #: remind th Service Name
    service = models.CharField('Service name', max_length=255, editable=False, null=True, default="")
    #: Should Waves Notify client about Job Status
    notify = models.BooleanField("Notify this result", default=False, editable=False)

    LOG_LEVEL = waves_settings.JOB_LOG_LEVEL

    @property
    def link(self):
        if self.client and 'waves.authentication' in settings.INSTALLED_APPS:
            # changer les variables d'url des templates
            return "{}{}".format(self.client.waves_user.main_domain, self.get_absolute_url())
        return super(Job, self).link

    @property
    def log_dir(self):
        return self.working_dir

    @property
    def logger_name(self):
        return 'waves.job.%s' % str(self.slug)

    @property
    def logger_file_name(self):
        return 'job.log'

    @property
    def status(self):
        """ Current last known job status """
        return self._status

    @status.setter
    def status(self, value):
        """ Set current status for job, and save state in job history

        :param value:
        :return: None
        """
        if value != self._status:
            message = "[{}] {}".format(value, smart_text(self.message)) if self.message else "New job status {}".format(
                value)
            logger.debug('JobHistory saved [%s][%s] status: %s', self.slug, self.get_status_display(), message)
            self.job_history.create(message=message, status=value)
        self._status = value

    def colored_status(self):
        """
        Format a row depending on current Job Status

        :return: Html unicode string
        """
        return format_html('<span class="{}">{}</span>', self.label_class, self.get_status_display())

    def job_service_back_url(self):
        """ Retrieve associated service url is exists """
        if self.submission and self.submission.service:
            return self.submission.service.get_admin_url()
        else:
            return "#"

    def make_job_dirs(self):
        """ Create job working dir """
        if not os.path.isdir(self.working_dir):
            os.makedirs(self.working_dir, mode=0o2775)

    def delete_job_dirs(self):
        """ Upon job deletion in database, cleanup associated working dirs """
        shutil.rmtree(self.working_dir, ignore_errors=True)

    @classmethod
    def from_db(cls, db, field_names, values):
        """ Overridden, set up _status to last DB value """
        instance = super(Job, cls).from_db(db, field_names, values)
        instance._status = instance.status
        return instance

    @property
    def changed_status(self):
        """ Tells whether loaded object status is different from the one issued from last retrieve in db

        :return: True if changed, False either
        :rtype: bool
        """
        return self._status != self.status

    @property
    def input_files(self):
        """ Get job files inputs

        :return: list of JobInput models instance
        :rtype: queryset
        """
        return self.job_inputs.filter(param_type=ParamType.TYPE_FILE)

    @property
    def output_files_exists(self):
        """ Check if expected outputs are present on disk, return only those ones

        :return: list of file path
        :rtype: list
        """
        all_outputs = self.outputs.all()
        existing = []
        for the_output in all_outputs:
            existing.append(
                dict(file_path=the_output.file_path,
                     name=os.path.basename(the_output.file_path),
                     api_name=the_output.get_api_name(),
                     label=the_output.name,
                     slug=the_output.slug,
                     available=os.path.isfile(the_output.file_path) and os.path.getsize(the_output.file_path) > 0))
        return existing

    @property
    def output_files(self):
        """
        Return list of all expected outputs files, whether they exist or not on disk

        .. note::
            Use :func:`output_files_exists` for only existing outputs instead

        :return: a list of JobOutput objects
        :rtype: list

        """
        return self.outputs.all()

    @property
    def input_params(self):
        """ Return tool params, i.e job execution parameters

        :return: list of `JobInput` models instance
        :rtype: [list of JobInput objects]
        """
        return self.job_inputs.exclude(param_type=ParamType.TYPE_FILE)

    @property
    def working_dir(self):
        """Base job working dir

        :return: working dir
        :rtype: unicode
        """
        from waves.settings import waves_settings
        return os.path.join(waves_settings.JOB_BASE_DIR, str(self.slug))

    @property
    def adaptor(self):
        """ Return current related service adapter effective class

        :return: a JobRunnerAdaptor
        :rtype: `waves.core.mocks.runner.JobRunnerAdaptor`
        """
        if self._adaptor:
            from waves.core.loader import AdaptorLoader
            try:
                adaptor = AdaptorLoader.unserialize(self._adaptor)
                return adaptor
            except Exception as e:
                self.logger.exception("Unable to load %s adapter %s", self._adaptor, e.message)
        elif self.submission:
            return self.submission.adaptor
        else:
            self.logger.exception("None adapter ...")
        return None

    @adaptor.setter
    def adaptor(self, value):
        self._adaptor = value.serialize()
        self.save(update_fields=["_adaptor"])

    def __str__(self):
        return '[{}][{}]'.format(self.slug, self.service)

    @property
    def command_parser(self):
        """ Return current related service command effective class
        """
        return self.submission.command_parser

    @property
    def command_line_arguments(self):
        """ Job command line finally executed on computing platform
        :return: string representation of command line
        :rtype: unicode
        """
        return "{}".format(
            self.command_parser.create_command_line(inputs=self.job_inputs.all().order_by('order')))

    @property
    def command_line(self):
        if self._command_line is None:
            self._command_line = "{} {}".format(self.submission.run_params.get('command'),
                                                self.command_line_arguments)
            self.save(update_fields=["_command_line"])
        return self._command_line

    @property
    def command(self):
        return self.submission.run_params.get('command')

    @property
    def label_class(self):
        """Return css class label associated with current Job Status

        :return: a css class (based on bootstrap)
        :rtype: unicode
        """
        if self.status in (JobStatus.JOB_UNDEFINED, JobStatus.JOB_SUSPENDED):
            return 'warning'
        elif self.status == JobStatus.JOB_ERROR:
            return 'danger'
        elif self.status == JobStatus.JOB_CANCELLED:
            return 'info'
        else:
            return 'success'

    def check_send_mail(self):
        """According to job status, check needs for sending notification emails

        :return: the nmmber of mail sent (should be one)
        :rtype: int
        """
        mailer = waves_settings.MAILER_CLASS()
        mailer.check_send_mail(self)

    def get_absolute_url(self):
        """Reverse url for this Job according to Django urls configuration

        :return: the absolute uri of this job (without host)
        """
        from django.urls import reverse
        return reverse('wcore:job_details', kwargs={'unique_id': self.slug})

    @property
    def stdout(self):
        """ Job standard output file

        :rtype: unicode
        """
        return 'job.stdout'

    @property
    def stderr(self):
        """ Job standard error file

        :rtype: unicode
        """
        return 'job.stderr'

    def create_non_editable_inputs(self):
        """
        Create non editable (i.e not submitted anywhere and used for run)

        :return: None
        """
        if self.submission:
            for service_input in self.submission.inputs.filter(required=None):
                # Create fake "submitted_inputs" with non editable ones with default value if not already set
                self.logger.debug('Created non editable job input: %s (%s, %s)', service_input.label,
                                  service_input.name, service_input.default)
                self.job_inputs.add(JobInput.objects.create(job=self, name=service_input.name,
                                                            param_type=service_input.type,
                                                            cmd_format=service_input.cmd_format,
                                                            label=service_input.label,
                                                            order=service_input.order,
                                                            value=service_input.default))

    def create_default_outputs(self):
        """ Create standard outputs for job (stdout and stderr) files

        :return: None
        """
        output_dict = dict(job=self, value=self.stdout, _name='Standard output')
        out = JobOutput.objects.create(**output_dict)
        self.outputs.add(out)
        std_file = join(self.working_dir, self.stdout)
        open(std_file, 'w').close()
        os.chmod(std_file, 0o664)
        output_dict['value'] = self.stderr
        output_dict['_name'] = "Standard error"
        out1 = JobOutput.objects.create(**output_dict)
        self.outputs.add(out1)
        std_file = join(self.working_dir, self.stderr)
        open(std_file, 'w').close()
        os.chmod(std_file, 0o664)

    @property
    def public_history(self):
        """ Filter Job history elements for public (non `JobAdminHistory` elements)

        :rtype: QuerySet
        """
        return self.job_history.filter(is_admin=False)

    @property
    def last_history(self):
        """ Retrieve last public history message """
        return self.public_history.first()

    def retry(self, message):
        """ Add a new try for job execution, save retry reason in JobAdminHistory, save job """
        if self.nb_retry <= waves_settings.JOBS_MAX_RETRY:
            self.nb_retry += 1
            if message is not None:
                self.job_history.create(message='[Retry] {}'.format(smart_text(message)), status=self.status)
            else:
                self.job_history.create(message='[Retry] {}'.format(self.get_status_display()), status=self.status)
        else:
            self.error(message)

    def error(self, message):
        """ Set job Status to ERROR, save error reason in JobAdminHistory, save job"""
        with open(join(self.working_dir, self.stderr), "a") as f:
            f.write('Job error: %s' % smart_text(message))
        self.message = '[Error] {}'.format(smart_text(message))
        self.status = JobStatus.JOB_ERROR

    def fatal_error(self, exception):
        logger.fatal('Job workflow fatal error: %s', exception)
        self.error(smart_text(exception.message))

    def get_status_display(self):
        return self.get__status_display()

    def _run_action(self, action):
        """
        Report action to specified job adapter

        :param action: action one of [prepare, run, cancel, status, results, retrieve_run_details]
        :return: None
        """
        try:
            if self.adaptor is None:
                raise WavesException("No Adapter, impossible to run")
            else:
                returned = getattr(self.adaptor, action)(self)
                self.nb_retry = 0
                return returned
        except AdaptorException as exc:
            self.retry(exc)
            # raise
        except JobInconsistentStateError:
            # raise log_exception, do not change job status
            raise
        except WavesException as exc:
            self.error(exc)
            raise
        except Exception as exc:
            self.fatal_error(exc)
            raise
        finally:
            self.save()

    @property
    def next_status(self):
        """ Automatically retrieve next expected status """
        if self.status in JobStatus.NEXT_STATUS:
            return JobStatus.NEXT_STATUS[self.status]
        else:
            return JobStatus.JOB_UNDEFINED

    def run_prepare(self):
        """ Ask job adapter to prepare run (manage input files essentially) """
        self._run_action('prepare_job')
        self.status = JobStatus.JOB_PREPARED

    def run_launch(self):
        """ Ask job adapter to actually launch job """
        self._run_action('run_job')
        self.status = JobStatus.JOB_QUEUED

    def run_status(self):
        """ Ask job adapter current job status """
        self._run_action('job_status')
        self.logger.debug('job current state :%s', self.status)
        if self.status == JobStatus.JOB_COMPLETED:
            self.run_results()
        if self.status == JobStatus.JOB_UNDEFINED and self.nb_retry > waves_settings.JOBS_MAX_RETRY:
            self.run_cancel()
        self.save()
        return self.status

    def run_cancel(self):
        """ Ask job adapter to cancel job if possible """
        self.message = 'Job cancelled'
        self._run_action('cancel_job')

    def run_results(self):
        """ Ask job adapter to get results files (dowload files if needed) """
        self._run_action('job_results')
        self.retrieve_run_details()
        self.logger.debug("Results %s %s %d", self.get_status_display(), self.exit_code,
                          os.stat(join(self.working_dir, self.stderr)).st_size)
        if os.stat(join(self.working_dir, self.stderr)).st_size > 0:
            logger.error('Error found %s %s ', self.exit_code, smart_text(self.stderr_txt))
            self.job_history.create(message='job.stderr is not empty', status=JobStatus.JOB_WARNING)
            self.status = JobStatus.JOB_WARNING
        else:
            self.message = "Data retrieved"
            self.status = JobStatus.JOB_FINISHED

    def retrieve_run_details(self):
        """ Ask job adapter to get JobRunDetails information (started, finished, exit_code ...)"""
        if self.run_details is None:
            file_run_details = join(self.working_dir, 'job_run_details.json')
            try:
                remote_details = self._run_action('job_run_details')
            except AdaptorException:
                remote_details = self.default_run_details()
            with open(file_run_details, 'w') as fp:
                json.dump(obj=remote_details, fp=fp, ensure_ascii=False)
            os.chmod(file_run_details, 0o664)
            return remote_details
        return self.run_details

    @property
    def run_details(self):
        file_run_details = join(self.working_dir, 'job_run_details.json')
        if os.path.isfile(file_run_details):
            # Details have already been downloaded
            try:
                with open(file_run_details) as fp:
                    details = JobRunDetails(*json.load(fp))
                return details
            except TypeError:
                self.logger.error("Unable to retrieve data from file %s", file_run_details)
                return self.default_run_details()
        return None

    @property
    def stdout_txt(self):
        """Retrieve stdout content for this job"""
        with open(join(self.working_dir, self.stdout), 'r') as fp:
            return fp.read()

    @property
    def stderr_txt(self):
        with open(join(self.working_dir, self.stderr), 'r') as fp:
            return fp.read()

    @property
    def allow_rerun(self):
        """ set whether current job state allow rerun """
        return self.status not in (JobStatus.JOB_CREATED, JobStatus.JOB_UNDEFINED)

    def re_run(self):
        """ Reset attributes and mark job as CREATED to be re-run"""
        # self.job_history.all().delete()
        self.nb_retry = 0
        self.job_history.all().update(is_admin=True)
        self.job_history.create(message='Marked for re-run', status=self.status)
        self.status = JobStatus.JOB_CREATED
        self._command_line = None

        for job_out in self.outputs.all():
            open(job_out.file_path, 'w').close()
        # Reset logs
        open(self.log_file, 'w').close()
        self.save()

    def default_run_details(self):
        """ Get and retriver a JobStatus.JobRunDetails namedtuple with defaults values"""
        prepared = self.job_history.filter(status=JobStatus.JOB_PREPARED).first()
        finished = self.job_history.filter(status__gte=JobStatus.JOB_COMPLETED).first()
        prepared_date = prepared.timestamp.isoformat() if prepared is not None else ""
        finished_date = finished.timestamp.isoformat() if finished is not None else ""
        return JobRunDetails(self.id, str(self.slug), self.remote_job_id, self.title, self.exit_code,
                             self.created.isoformat(), prepared_date, finished_date, '')

    def available_for_user(self, user):
        """ Access rules for submission form according to user
        :param user: Request User
        :return: boolean
        """
        # RULES to set if user can access service page
        return True


class JobInput(Ordered, Slugged, ApiModel, UrlMixin):
    """
    Job Inputs is association between a Job, a SubmissionParam, setting a value specific for this job
    """

    class Meta:
        unique_together = ('name', 'value', 'job')
        db_table = 'wcore_jobinput'
        app_label = "waves"

    objects = JobInputManager()
    #: Reference to related :class:`waves.core.models.jobs.Job`
    job = models.ForeignKey(Job, related_name='job_inputs', on_delete=models.CASCADE)
    #: Value set to this service input for this job
    value = models.CharField('Input content', max_length=255, null=True,
                             blank=True,
                             help_text='Input value (filename, boolean value, int value etc.)')
    #: Each input may have its own identifier on remote adapter
    remote_input_id = models.CharField('Remote input ID (on adapter)',
                                       max_length=255,
                                       editable=False, null=True)
    #: retrieved upon creation from related AParam object
    param_type = models.CharField('Param param_type', choices=ParamType.IN_TYPE,
                                  max_length=50, editable=False,
                                  null=True)
    #: retrieved upon creation from related AParam object
    name = models.CharField('Param name', max_length=50, editable=False, null=True)
    #: retrieved upon creation from related AParam object
    cmd_format = models.IntegerField('Parameter Type', choices=OptType.OPT_TYPE, editable=False, null=True,
                                     default=OptType.OPT_TYPE_POSIX)
    #: retrieved upon creation from related AParam object
    label = models.CharField('Label', max_length=100, editable=False, null=True)

    @property
    def link(self):
        if self.job.client and 'waves.authentication' in settings.INSTALLED_APPS:
            # changer les variables d'url des templates
            return "{}{}".format(self.job.client.waves_user.main_domain, self.get_absolute_url())
        return super(JobInput, self).link()

    @property
    def required(self):
        return True

    def save(self, *args, **kwargs):
        super(JobInput, self).save(*args, **kwargs)

    def __str__(self):
        return u'%s' % self.name

    @property
    def file_path(self):
        """Absolute file path to associated file (if any)

        :return: path to file
        :rtype: unicode
        """
        if self.param_type == ParamType.TYPE_FILE:
            return os.path.join(self.job.working_dir, str(self.value))
        else:
            return ""

    @property
    def file_name(self):
        if self.param_type == ParamType.TYPE_FILE:
            return self.value
        else:
            return ""

    @property
    def validated_value(self):
        """ May modify value (cast) according to related SubmissionParam type

        :return: determined from related SubmissionParam type
        """
        if self.param_type in (ParamType.TYPE_FILE, ParamType.TYPE_TEXT):
            return self.value
        elif self.param_type == ParamType.TYPE_BOOLEAN:
            return bool(self.value)
        elif self.param_type == ParamType.TYPE_INT:
            return int(self.value)
        elif self.param_type == ParamType.TYPE_DECIMAL:
            return float(self.value)
        elif self.param_type == ParamType.TYPE_LIST:
            if self.value == 'None':
                return False
            return self.value
        else:
            raise ValueError("No type specified for input")

    @property
    def srv_input(self):
        if self.job.submission:
            return self.job.submission.inputs.filter(name=self.name).first()
        raise RuntimeError('Missing submission for this job')

    def clean(self):
        if self.srv_input.mandatory and not self.srv_input.default and not self.value:
            raise ValidationError('Input %(input) is mandatory', params={'input': self.srv_input.label})
        super(JobInput, self).clean()

    @property
    def get_label_for_choice(self):
        """ Try to get label for value issued from a service list input"""
        from waves.models import AParam
        try:
            srv_input = AParam.objects.get(submission=self.job.submission,
                                           name=self.name)
            return srv_input.choices(self.value) if hasattr(srv_input, 'choices') else self.value
        except ObjectDoesNotExist:
            pass
        return self.value

    @property
    def display_online(self):
        return allow_display_online(self.file_path)

    @property
    def download_url(self):
        if self.available:
            return "%s?export=1" % self.get_absolute_url()
        else:
            return "#"

    @property
    def available(self):
        return self.param_type == ParamType.TYPE_FILE and os.path.isfile(self.file_path) \
               and os.path.getsize(self.file_path) > 0

    def get_absolute_url(self):
        """Reverse url for this Job according to Django urls configuration

        :return: the absolute uri of this job (without host)
        """
        from django.urls import reverse
        return reverse('wcore:job_input', kwargs={'slug': self.slug})

    def duplicate_api_name(self, api_name):
        """ Check is another entity is set with same api_name

        :param api_name:
        """
        return self.__class__.objects.filter(api_name=api_name, job=self.job).exclude(pk=self.pk)


class JobOutput(Ordered, Slugged, UrlMixin, ApiModel):
    """ JobOutput is association fro a Job, a SubmissionOutput, and the effective value set for this Job
    """

    class Meta:
        unique_together = ('api_name', 'job')
        db_table = 'wcore_joboutput'
        app_label = "waves"

    objects = JobOutputManager()
    field_api_name = "_name"
    #: Related :class:`waves.core.models.jobs.Job`
    job = models.ForeignKey(Job, related_name='outputs', on_delete=models.CASCADE)
    #: Related :class:`waves.core.models.services.SubmissionOutput`
    # srv_output = models.ForeignKey('SubmissionOutput', null=True, on_delete=models.CASCADE)
    #: Job Output value
    value = models.CharField('Output value', max_length=200, null=True, blank=True, default="")
    #: Each output may have its own identifier on remote adaptor
    remote_output_id = models.CharField('Remote output ID (on adapter)', max_length=255, editable=False, null=True)
    _name = models.CharField('Name', max_length=50, null=False, blank=False, help_text='Output displayed name')
    extension = models.CharField('File extension', max_length=5, null=False, default="")

    @property
    def link(self):
        if self.job.client and 'waves.authentication' in settings.INSTALLED_APPS:
            # changer les variables d'url des templates
            return "{}{}".format(self.job.client.waves_user.main_domain, self.get_absolute_url())
        return super(JobOutput, self).link()

    @property
    def name(self):
        # hard coded value for non service related output (stderr / stdout)
        if self.value == self.job.stdout:
            return "Standard output"
        elif self.value == self.job.stderr:
            return "Standard error"
        return self._name

    def get_extension(self):
        if self.value == self.job.stdout:
            return ".stdout"
        elif self.value == self.job.stderr:
            return ".stderr"
        return self.extension

    @name.setter
    def name(self, value):
        self._name = value

    def get_api_name(self):
        if self.value == self.job.stdout:
            return "standard_output"
        elif self.value == self.job.stderr:
            return "standard_error"
        return self.api_name

    def __str__(self):
        return '%s - %s' % (self.name, self.value)

    @property
    def file_name(self):
        return self.value

    @property
    def file_path(self):
        if self.value == self.job.stdout:
            return os.path.join(self.job.working_dir, self.job.stdout)
        elif self.value == self.job.stderr:
            return os.path.join(self.job.working_dir, self.job.stderr)
        return os.path.join(self.job.working_dir, self.file_name)

    @property
    def file_content(self):
        if os.path.isfile(self.file_path):
            with open(self.file_path, 'r') as f:
                return f.read()
        return None

    def get_absolute_url(self):
        from django.urls import reverse
        return "%s?export=1" % reverse('wcore:job_output', kwargs={'slug': self.slug})

    @property
    def download_url(self):
        if self.available:
            return "%s?export=1" % self.get_absolute_url()
        else:
            return "#"

    @property
    def display_online(self):
        return allow_display_online(self.file_path)

    @property
    def available(self):
        return os.path.isfile(self.file_path) and os.path.getsize(self.file_path) > 0

    def duplicate_api_name(self, api_name):
        """ Check is another entity is set with same api_name

        :param api_name:
        """
        return self.__class__.objects.filter(api_name=api_name, job=self.job).exclude(pk=self.pk)
