""" WAVES job related models class objects """
from __future__ import unicode_literals

import json
import logging
import os
import six
from os import path as path
from os.path import join

import swapper
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.db import models, transaction
from django.db.models import Q
from django.utils.encoding import smart_text
from django.utils.html import format_html

import waves.wcore.adaptors.exceptions
from waves.wcore.adaptors.const import *
from waves.wcore.adaptors.mails import JobMailer
from waves.wcore.exceptions import WavesException
from waves.wcore.exceptions.jobs import *
from waves.wcore.models import TimeStamped, Slugged, Ordered, UrlMixin, ApiModel, FileInputSample, \
    SubmissionOutput
from waves.wcore.models.const import *
from waves.wcore.settings import waves_settings
from waves.wcore.utils import random_analysis_name
from waves.wcore.utils.storage import allow_display_online

logger = logging.getLogger(__name__)

__all__ = ['Job', 'JobInput', 'JobOutput', 'JobManager']


class JobManager(models.Manager):
    """ Job Manager add few shortcut function to default Django models objects Manager
    """

    def get_by_natural_key(self, slug, service):
        return self.get(slug=slug, service=service)

    def get_all_jobs(self):
        """
        Return all jobs currently registered in database, as list of dictionary elements
        :return: QuerySet
        """
        return self.all().values()

    def get_user_job(self, user):
        """
        Filter jobs according to user (logged in) according to following access rule:
        * User is a super_user, return all jobs
        * User is member of staff (access to Django admin): returns only jobs from services user has created,
        jobs created by user, or where associated email is its email
        * User is simply registered on website, returns only those created by its own
        :param user: current user (may be Anonymous)
        :return: QuerySet
        """
        if not user or user.is_anonymous:
            return self.none()
        if user.is_superuser:
            return self.all()
        if user.is_staff:
            return self.filter(Q(service__created_by=user) | Q(client=user) | Q(email_to=user.email))
        return self.filter(client=user)

    @staticmethod
    def add_filter_user(queryset, user):
        if not user or user.is_anonymous:
            return queryset.none()
        if user.is_superuser:
            return queryset
        if user.is_staff:
            return queryset.filter(Q(service__created_by=user) | Q(client=user) | Q(email_to=user.email))
        return queryset.filter(client=user)

    def get_service_job(self, user, service):
        """
        Returns jobs filtered by service, according to following access rule:
        * user is simply registered, return its jobs, filtered by service
        :param user: currently logged in user
        :param service: service model object to filter
        :return: QuerySet
        """
        if not user or user.is_anonymous:
            return self.none()
        if user.is_superuser or user.is_staff:
            return self.filter(submission__service__in=[service, ])
        return self.filter(client=user, submission__service__in=[service, ])

    def get_submission_job(self, user, submission):
        """
        Returns jobs filtered by service, according to following access rule:
        * user is simply registered, return its jobs, filtered by service
        :param user: currently logged in user
        :param submission: submission model object to filter
        :return: QuerySet
        """
        if not user or user.is_anonymous:
            return self.none()
        if user.is_superuser or user.is_staff:
            return self.filter(submission=submission)
        return self.filter(client=user, submission=submission)

    def get_pending_jobs(self, user=None):
        """
        Return pending jobs for user, according to following access rule:
        * user is simply registered, return its jobs, filtered by service
        :param user: currently logged in user
        :return: QuerySet

        .. note::
            Pending jobs are all jobs which are 'Created', 'Prepared', 'Queued', 'Running'
        """
        if user and not user.is_anonymous:
            if user.is_superuser or user.is_staff:
                # return all pending jobs
                return self.filter(_status__in=(
                    JOB_CREATED,
                    JOB_PREPARED,
                    JOB_QUEUED,
                    JOB_RUNNING))
            # get only user jobs
            return self.filter(_status__in=(JOB_CREATED,
                                            JOB_PREPARED,
                                            JOB_QUEUED,
                                            JOB_RUNNING),
                               client=user)
        # User is not supposed to be None
        return self.none()

    def get_created_job(self, extra_filter, user=None):
        """
        Return pending jobs for user, according to following access rule:
        * user is simply registered, return its jobs, filtered by service
        :param extra_filter: add an extra filter to queryset
        :param user: currently logged in user
        :return: QuerySet
        """
        if user is not None:
            self.filter(status=JOB_CREATED,
                        client=user,
                        **extra_filter).order_by('-created')
        return self.filter(_status=JOB_CREATED,
                           **extra_filter).order_by('-created').all()

    @transaction.atomic
    def create_from_submission(self, submission, submitted_inputs,
                               email_to=None, user=None,
                               force_status=None, update=None):
        """ Create a new job from service submission data and submitted inputs values
        :type update: Existing Job to extend
        :param force_status: Force initial job status
        :param submission: Dictionary { param_name: param_value }
        :param submitted_inputs: received input from client submission
        :param email_to: if given, email address to notify job process to
        :param user: associated user (may be anonymous)
        :return: a newly create Job instance
        :rtype: :class:`waves.wcore.models.jobs.Job`
        """
        default_email = user.email if user and not user.is_anonymous() else None
        follow_email = email_to or default_email

        if update is None:
            job = self.create(email_to=follow_email, client=user,
                              title=submitted_inputs.get('title', None),
                              submission=submission,
                              service=submission.service.name,
                              _adaptor=submission.adaptor.serialize(),
                              notify=submission.service.email_on)
        else:
            job = update
            job.submission = submission
            job.adaptor = submission.adaptor
            job.notify = submission.service.email_on
            job.service = submission.service.name
        if job.logger.isEnabledFor(logging.DEBUG):
            job.logger.debug('Received data :')
            for key in submitted_inputs:
                job.logger.debug('Param %s: %s', key, submitted_inputs[key])
        mandatory_params = submission.expected_inputs.filter(required=True)
        missing = {m.name: '%s (:%s:) is required field' % (m.label, m.api_name) for m in mandatory_params if
                   m.api_name not in submitted_inputs.keys()}
        if len(missing) > 0:
            logger.warning("received keys %s", submitted_inputs.keys())
            logger.warning("Expected mandatory %s missing", [(m.label, m.api_name) for m in mandatory_params])
            raise ValidationError(missing)
        # First create inputs
        submission_inputs = submission.inputs.filter(api_name__in=submitted_inputs.keys()).exclude(required=None)
        for service_input in submission_inputs:
            # Treat only non dependent inputs first
            incoming_input = submitted_inputs.get(service_input.api_name, None)
            logger.debug("Current Service Input: %s, %s, %s", service_input, service_input.required, incoming_input)
            # test service input mandatory, without default and no value
            if service_input.required and not service_input.default and incoming_input is None:
                raise JobMissingMandatoryParam(service_input.label, job)
            if incoming_input:
                logger.debug('Retrieved "%s" for service input "%s:%s"', incoming_input, service_input.label,
                             service_input.name)
                # transform single incoming into list to keep process iso
                if type(incoming_input) != list:
                    incoming_input = [incoming_input]
                for in_input in incoming_input:
                    job.job_inputs.add(
                        JobInput.objects.create_from_submission(job, service_input, service_input.order, in_input))

        # create expected outputs
        for service_output in submission.outputs.all():
            job.outputs.add(
                JobOutput.objects.create_from_submission(job, service_output, submitted_inputs))
        job.logger.debug('Job %s created with %i inputs', job.slug, job.job_inputs.count())
        if job.logger.isEnabledFor(logging.DEBUG):
            # LOG full command line
            logger.debug('Job %s command will be :', job.title)
            logger.debug('Job %s command will be :', job.title)
            logger.debug('%s %s', job.adaptor.command, job.command_line)
            logger.debug('Expected outputs will be:')
            for j_output in job.outputs.all():
                logger.debug('Output %s: %s', j_output.name, j_output.value)
                logger.debug('Output %s: %s', j_output.name, j_output.value)
        job._command_line = job.command_line
        if force_status is not None and force_status in STATUS_MAP.keys():
            job.status = force_status
        job.save()
        return job


class Job(TimeStamped, Slugged, UrlMixin):
    """
    A job represent a request for executing a service, it requires values from specified required input from related
    service
    """
    # non persistent field, used for history savings see signals
    #: Current message associated with job object, not directly stored in job table, but in history
    message = None
    #: Job status time (for history)
    status_time = None
    #: Job run details retrieved or not
    _run_details = None

    class Meta(TimeStamped.Meta):
        verbose_name = 'Job'
        verbose_name_plural = "Jobs"
        ordering = ['-updated', '-created']

    objects = JobManager()
    #: Job Title, automatic or set by user upon submission
    title = models.CharField('Job title', max_length=255, null=True, blank=True)
    #: Job related Service
    submission = models.ForeignKey(swapper.get_model_name('wcore', 'Submission'), related_name='service_jobs',
                                   null=True, on_delete=models.SET_NULL)
    #: Job status issued from last retrieve on DB
    _status = models.IntegerField('Job status', choices=STATUS_LIST,
                                  default=JOB_CREATED)
    #: Job last status for which we sent a notification email
    status_mail = models.IntegerField(editable=False, default=9999)
    #: Job associated client, may be null for anonymous submission
    client = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE,
                               related_name='clients_job', help_text='Associated registered user')
    #: Email to notify job status to
    email_to = models.EmailField('Email results', null=True, blank=True, help_text='Notify results to this email')
    #: Job ExitCode (mainly for admin purpose)
    exit_code = models.IntegerField('Job system exit code', default=0, help_text="Job exit code on relative adaptor")
    #: Tell whether job results files are available for download from client
    results_available = models.BooleanField('Results are available', default=False, editable=False)
    #: Job last status retry count (max before Error set in conf)
    nb_retry = models.IntegerField('Nb Retry', editable=False, default=0)
    #: Jobs are remotely executed, store the adaptor job identifier
    remote_job_id = models.CharField('Remote job ID', max_length=255, editable=False, null=True)
    #: Jobs sometime can gain access to a remote history, store the adaptor history identifier
    remote_history_id = models.CharField('Remote history ID', max_length=255, editable=False, null=True)
    #: Final generated command line
    _command_line = models.CharField('Final generated command line', max_length=255, editable=False, null=True)
    #: adaptor serialized values
    _adaptor = models.TextField('Adaptor classed used for this Job', editable=False, null=True)
    #: remind th Service Name
    service = models.CharField('Service name', max_length=255, editable=False, null=True, default="")
    #: Should Waves Notify client about Job Status
    notify = models.BooleanField("Notify this result", default=False, editable=False)

    _logger = None

    @property
    def log_file(self):
        return os.path.join(self.working_dir, 'job.log')

    @property
    def logger(self):
        self._logger = logging.getLogger('waves.job.%s' % str(self.slug))
        if not len(self._logger.handlers):
            # Add handler only once !
            hdlr = logging.FileHandler(self.log_file)
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            hdlr.setFormatter(formatter)
            self._logger.propagate = False
            self._logger.addHandler(hdlr)
            self._logger.setLevel(waves_settings.JOB_LOG_LEVEL)
        return self._logger

    @property
    def random_title(self):
        return "Job %s-%s" % (self.service,
                              random_analysis_name())

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value != self._status:
            message = smart_text(self.message) or ""
            self.logger.debug('JobHistory saved [%s] status: %s', self.get_status_display(),
                              message)
            self.job_history.create(message=message, status=value)
        self._status = value

    def colored_status(self):
        """
        Format a row depending on current Job Status
        :return: Html unicode string
        """
        return format_html('<span class="{}">{}</span>', self.label_class, self.get_status_display())

    def job_service_back_url(self):
        if self.submission and self.submission.service:
            return self.submission.service.get_admin_url()
        else:
            return "#"

    def save(self, *args, **kwargs):
        """ Overriden save, set _status to current job status """
        super(Job, self).save(*args, **kwargs)

    def make_job_dirs(self):
        """
        Create job working dirs
        :return: None
        """
        if not os.path.isdir(self.working_dir):
            os.makedirs(self.working_dir, mode=0775)

    def delete_job_dirs(self):
        """Upon job deletion in database, cleanup associated working dirs
        :return: None
        """
        import shutil
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
        """ Get only 'files' inputs for job
        :return: list of JobInput models instance
        :rtype: QuerySet
        """
        return self.job_inputs.filter(param_type=TYPE_FILE)

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
        Return list of all outputs files, whether they exist or not on disk
            .. note::
                Use :func:`output_files_exists` for only existing outputs instead

        :return: a list of JobOutput objects
        :rtype: list

        """
        all_files = self.outputs.all()
        return all_files

    @property
    def input_params(self):
        """ Return all non-file (i.e tool params) job inputs, i.e job execution parameters
        :return: list of `JobInput` models instance
        :rtype: [list of JobInput objects]
        """
        return self.job_inputs.exclude(param_type=TYPE_FILE)

    @property
    def working_dir(self):
        """Base job working dir

        :return: working dir
        :rtype: unicode
        """
        from waves.wcore.settings import waves_settings
        return os.path.join(waves_settings.JOB_BASE_DIR, str(self.slug))

    @property
    def adaptor(self):
        """ Return current related service adaptor effective class
        :return: a child class of `JobRunnerAdaptor`
        :rtype: `waves.wcore.adaptors.runner.JobRunnerAdaptor`
        """
        if self._adaptor:
            from waves.wcore.adaptors.loader import AdaptorLoader
            try:
                adaptor = AdaptorLoader.unserialize(self._adaptor)
                return adaptor
            except Exception as e:
                self.logger.exception("Unable to load %s adaptor %s", self._adaptor, e.message)
        elif self.submission:
            return self.submission.adaptor
        else:
            self.logger.exception("None adaptor ...")
        return None

    @adaptor.setter
    def adaptor(self, value):
        self._adaptor = value.serialize()
        self.save(update_fields=["_adaptor"])

    def __str__(self):
        return '[%s][%s]' % (self.slug, self.service)

    @property
    def command(self):
        """ Return current related service command effective class
        :return: a BaseCommand object (or one of its child)
        :rtype: `BaseCommand`
        """
        from waves.wcore.commands.command import BaseCommand
        return BaseCommand()

    @property
    def command_line(self):
        """ Generate full command line for Job
        :return: string representation of command line
        :rtype: unicode
        """
        if self._command_line is None:
            self.command_line = "%s" % self.command.create_command_line(inputs=self.job_inputs.all().order_by('order'))
        return self._command_line

    @command_line.setter
    def command_line(self, command_line):
        self._command_line = command_line
        self.save(update_fields=['_command_line'])

    @property
    def label_class(self):
        """Return css class label associated with current Job Status
        :return: a css class (based on bootstrap)
        :rtype: unicode
        """
        if self.status in (JOB_UNDEFINED, JOB_SUSPENDED):
            return 'warning'
        elif self.status == JOB_ERROR:
            return 'danger'
        elif self.status == JOB_CANCELLED:
            return 'info'
        else:
            return 'success'

    def check_send_mail(self):
        """According to job status, check needs for sending notification emails
        :return: the nmmber of mail sent (should be one)
        :rtype: int
        """
        mailer = JobMailer()
        if self.status != self.status_mail and self.status == JOB_ERROR:
            mailer.send_job_admin_error(self)
        if waves_settings.NOTIFY_RESULTS and self.notify:
            if self.email_to is not None and self.status != self.status_mail:
                # should send a email
                try:
                    nb_sent = 0
                    if self.status == JOB_CREATED:
                        nb_sent = mailer.send_job_submission_mail(self)
                    elif self.status == JOB_TERMINATED:
                        nb_sent = mailer.send_job_completed_mail(self)
                    elif self.status == JOB_ERROR:
                        nb_sent = mailer.send_job_error_email(self)
                    elif self.status == JOB_CANCELLED:
                        nb_sent = mailer.send_job_cancel_email(self)
                    # Avoid resending emails when last status mail already sent
                    self.status_mail = self.status
                    self.logger.info("Try to send email to %s [%s]", self.email_to, self.status)
                    if nb_sent > 0:
                        self.job_history.create(message='Sent notification email', status=self.status, is_admin=True)
                    else:
                        self.job_history.create(message='Mail not sent', status=self.status, is_admin=True)
                    self.save()
                    return nb_sent
                except Exception as e:
                    logger.error('Mail error: %s %s', e.__class__.__name__, e.message)
                    pass
            elif not self.email_to:
                self.logger.warn('Job %s email not set', self.slug)
        else:
            self.logger.info('Jobs notification are not activated')

    def get_absolute_url(self):
        """Reverse url for this Job according to Django urls configuration
        :return: the absolute uri of this job (without host)
        """
        from django.core.urlresolvers import reverse
        return reverse('wcore:job_details', kwargs={'slug': self.slug})

    @property
    def details_available(self):
        """Check whether run details are available for this JOB

        .. note::
            Not really yet implemented

        :return: True is exists, False either
        :rtype: bool
        """
        return os.path.isfile(os.path.join(self.working_dir, 'run_details.p'))

    @property
    def stdout(self):
        """ Hard coded job standard output file name

        :rtype: unicode
        """
        return 'job.stdout'

    @property
    def stderr(self):
        """ Hard coded job standard error file name

        :rtype: unicode
        """
        return 'job.stderr'

    def create_non_editable_inputs(self):
        """
        Create non editable (i.e not submitted anywhere and used for run)
            .. seealso::
                Used in post_save signals

        :param service_submission
        :return: None
        """

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
        """ Create standard default outputs for job (stdout and stderr)
        :return: None
        """
        output_dict = dict(job=self, value=self.stdout, _name='Standard output')
        out = JobOutput.objects.create(**output_dict)
        self.outputs.add(out)
        open(join(self.working_dir, self.stdout), 'w').close()
        output_dict['value'] = self.stderr
        output_dict['_name'] = "Standard error"
        out1 = JobOutput.objects.create(**output_dict)
        self.outputs.add(out1)
        open(join(self.working_dir, self.stderr), 'w').close()

    @property
    def public_history(self):
        """Filter Job history elements for public (non `JobAdminHistory` elements)

        :rtype: QuerySet
        """
        return self.job_history.filter(is_admin=False)

    def retry(self, message):
        """ Add a new try for job execution, save retry reason in JobAdminHistory, save job """
        if self.nb_retry <= waves_settings.JOBS_MAX_RETRY:
            self.nb_retry += 1
            if message is not None:
                self.job_history.create(message='[Retry]%s' % smart_text(message), status=self.status)
        else:
            self.error(message)

    def error(self, message):
        """ Set job Status to ERROR, save error reason in JobAdminHistory, save job"""
        self.logger.error('Job error: %s', smart_text(message))
        self.message = '[Error]%s' % smart_text(message)
        self.status = JOB_ERROR

    def fatal_error(self, exception):
        logger.fatal('Job workflow fatal error: %s', exception)
        self.error(smart_text(exception.message))

    def get_status_display(self):
        return self.get__status_display()

    def _run_action(self, action):
        """
        Report action to specified job adaptor
        :param action: action one of [prepare, run, cancel, status, results, run_details]
        :return: None
        """
        try:
            if self.adaptor is None:
                raise WavesException("No Adaptor, impossible to run")
            else:
                returned = getattr(self.adaptor, action)(self)
                self.nb_retry = 0
                return returned
        except waves.wcore.adaptors.exceptions.AdaptorException as exc:
            self.retry(exc.message)
            # raise
        except JobInconsistentStateError:
            # raise log_exception, do not change job status
            raise
        except WavesException as exc:
            self.error(exc.message)
            raise
        except Exception as exc:
            self.fatal_error(exc)
            raise
        finally:
            self.save()

    @property
    def next_status(self):
        """ Automatically retrieve next expected status """
        if self.status in NEXT_STATUS:
            return NEXT_STATUS[self.status]
        else:
            return JOB_UNDEFINED

    def run_prepare(self):
        """ Ask job adaptor to prepare run (manage input files essentially) """
        self._run_action('prepare_job')
        self.status = JOB_PREPARED

    def run_launch(self):
        """ Ask job adaptor to actually launch job """
        self._run_action('run_job')
        self.status = JOB_QUEUED

    def run_status(self):
        """ Ask job adaptor current job status """
        self._run_action('job_status')
        self.logger.debug('job current state :%s', self.status)
        if self.status == JOB_COMPLETED:
            self.run_results()
        if self.status == JOB_UNDEFINED and self.nb_retry > waves_settings.JOBS_MAX_RETRY:
            self.run_cancel()
        self.save()
        return self.status

    def run_cancel(self):
        """ Ask job adaptor to cancel job if possible """
        self._run_action('cancel_job')
        self.message = 'Job cancelled'
        self.status = JOB_CANCELLED

    def run_results(self):
        """ Ask job adaptor to get results files (dowload files if needed) """
        self._run_action('job_results')
        self.run_details()
        self.logger.debug("Results %s %s %d", self.get_status_display(), self.exit_code,
                          os.stat(join(self.working_dir, self.stderr)).st_size)
        if self.exit_code != 0:
            if os.stat(join(self.working_dir, self.stderr)).st_size > 0:
                logger.error('Error found %s %s ', self.exit_code, smart_text(self.stderr_txt))
            self.message = "Error detected in job.stderr"
            self.status = JOB_ERROR
        else:
            if os.stat(join(self.working_dir, self.stderr)).st_size > 0:
                self.status = JOB_WARNING
                logger.warning('Exit Code %s but found stderr %s ', self.exit_code,
                               smart_text(self.stderr_txt))
            else:
                self.message = "Data retrieved"
                self.status = JOB_TERMINATED

    def run_details(self):
        """ Ask job adaptor to get JobRunDetails information (started, finished, exit_code ...)"""

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
        else:
            try:
                remote_details = self._run_action('job_run_details')
            except waves.wcore.adaptors.exceptions.AdaptorException:
                remote_details = self.default_run_details()
            with open(file_run_details, 'w') as fp:
                json.dump(obj=remote_details, fp=fp, ensure_ascii=False)
            return remote_details

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
        return self.status not in (JOB_CREATED, JOB_UNDEFINED)

    def re_run(self):
        """ Reset attributes and mark job as CREATED to be re-run"""
        # self.job_history.all().delete()
        self.nb_retry = 0
        self.job_history.all().update(is_admin=True)
        self.job_history.create(message='Marked for re-run', status=self.status)
        self.status = JOB_CREATED
        self._command_line = None

        for job_out in self.outputs.all():
            open(job_out.file_path, 'w').close()
        # Reset logs
        open(self.log_file, 'w').close()
        self.save()

    def default_run_details(self):
        """ Get and retriver a JobRunDetails namedtuple with defaults values"""
        prepared = self.job_history.filter(status=JOB_PREPARED).first()
        finished = self.job_history.filter(status__gte=JOB_COMPLETED).first()
        prepared_date = prepared.timestamp.isoformat() if prepared is not None else ""
        finished_date = finished.timestamp.isoformat() if finished is not None else ""
        return JobRunDetails(self.id, str(self.slug), self.remote_job_id, self.title, self.exit_code,
                             self.created.isoformat(), prepared_date, finished_date, '')


class JobInputManager(models.Manager):
    """ JobInput model Manager """

    def get_by_natural_key(self, job, name):
        return self.get(job=job, name=name)

    def create(self, **kwargs):
        # Backward compatibility hack
        sin = kwargs.pop('srv_input', None)
        if sin:
            kwargs.update(dict(name=sin.name, param_type=sin.type, cmd_format=sin.cmd_line_type, label=sin.label))
        return super(JobInputManager, self).create(**kwargs)

    @transaction.atomic
    def create_from_submission(self, job, service_input, order, submitted_input):
        """
        :param job: The current job being created,
        :param service_input: current service submission input
        :param order: given order in future command line creation (if needed)
        :param submitted_input: received value for this service submission input
        :return: return the newly created JobInput
        :rtype: :class:`waves.wcore.models.jobs.JobInput`
        """
        input_dict = dict(job=job,
                          order=order,
                          name=service_input.name,
                          param_type=service_input.param_type,
                          api_name=service_input.api_name,
                          cmd_format=service_input.cmd_format,
                          label=service_input.label,
                          value=str(submitted_input))
        if service_input.param_type == TYPE_FILE:
            if isinstance(submitted_input, File):
                # classic uploaded file
                filename = path.join(job.working_dir, submitted_input.name)
                with open(filename, 'wb+') as uploaded_file:
                    for chunk in submitted_input.chunks():
                        uploaded_file.write(chunk)
                        # input_dict.update(dict(value='inputs/' + submitted_input.name))
            elif isinstance(submitted_input, (int, long)):
                # Manage sample data
                input_sample = FileInputSample.objects.get(pk=submitted_input)
                filename = path.join(job.working_dir, path.basename(input_sample.file.name))
                # input_dict['command_type'] = input_sample.file_input.cmd_format
                input_dict['value'] = path.basename(input_sample.file.name)
                with open(filename, 'wb+') as uploaded_file:
                    for chunk in input_sample.file.chunks():
                        uploaded_file.write(chunk)
            elif isinstance(submitted_input, (str, unicode)):
                # copy / paste content
                if service_input.default:
                    filename = path.join(job.working_dir, service_input.default)
                    input_dict.update(dict(value=service_input.default))
                else:
                    filename = path.join(job.working_dir, service_input.name + '.txt')
                    input_dict.update(dict(value=service_input.name + '.txt'))
                with open(filename, 'wb+') as uploaded_file:
                    uploaded_file.write(submitted_input)
            else:
                logger.warn("Unable to determine usable type for input %s:%s " % (service_input.name, submitted_input))
        new_input = self.create(**input_dict)
        return new_input


class JobInput(Ordered, Slugged, ApiModel):
    """
    Job Inputs is association between a Job, a SubmissionParam, setting a value specific for this job
    """

    class Meta:
        unique_together = ('name', 'value', 'job')

    objects = JobInputManager()
    #: Reference to related :class:`waves.wcore.models.jobs.Job`
    job = models.ForeignKey(Job, related_name='job_inputs', on_delete=models.CASCADE)
    #: Value set to this service input for this job
    value = models.CharField('Input content', max_length=255, null=True, blank=True,
                             help_text='Input value (filename, boolean value, int value etc.)')
    #: Each input may have its own identifier on remote adaptor
    remote_input_id = models.CharField('Remote input ID (on adaptor)', max_length=255, editable=False, null=True)
    #: retrieved upon creation from related AParam object
    param_type = models.CharField('Param param_type', choices=IN_TYPE, max_length=50, editable=False, null=True)
    #: retrieved upon creation from related AParam object
    name = models.CharField('Param name', max_length=50, editable=False, null=True)
    #: retrieved upon creation from related AParam object
    cmd_format = models.IntegerField('Parameter Type', choices=OPT_TYPE, editable=False, null=True,
                                     default=OPT_TYPE_POSIX)
    #: retrieved upon creation from related AParam object
    label = models.CharField('Label', max_length=100, editable=False, null=True)

    def natural_key(self):
        return self.job.natural_key(), self.name

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
        if self.param_type == TYPE_FILE:
            return os.path.join(self.job.working_dir, str(self.value))
        else:
            return ""

    @property
    def file_name(self):
        if self.param_type == TYPE_FILE:
            return self.value
        else:
            return ""

    @property
    def validated_value(self):
        """ May modify value (cast) according to related SubmissionParam type

        :return: determined from related SubmissionParam type
        """
        if self.param_type in (TYPE_FILE, TYPE_TEXT):
            return self.value
        elif self.param_type == TYPE_BOOLEAN:
            return bool(self.value)
        elif self.param_type == TYPE_INT:
            return int(self.value)
        elif self.param_type == TYPE_DECIMAL:
            return float(self.value)
        elif self.param_type == TYPE_LIST:
            if self.value == 'None':
                return False
            return self.value
        else:
            raise ValueError("No type specified for input")

    @property
    def srv_input(self):
        return self.job.submission.inputs.filter(name=self.name).first()

    def clean(self):
        if self.srv_input.mandatory and not self.srv_input.default and not self.value:
            raise ValidationError('Input %(input) is mandatory', params={'input': self.srv_input.label})
        super(JobInput, self).clean()

    @property
    def get_label_for_choice(self):
        # TODO check if still used !
        """ Try to get label for value issued from a service list input"""
        from waves.wcore.models.inputs import AParam
        try:
            srv_input = AParam.objects.get(submission=self.job.submission,
                                           name=self.name)
            return srv_input.get_choices(self.value)
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
        return self.param_type == TYPE_FILE and os.path.isfile(self.file_path) \
               and os.path.getsize(self.file_path) > 0

    def get_absolute_url(self):
        """Reverse url for this Job according to Django urls configuration
        :return: the absolute uri of this job (without host)
        """
        from django.core.urlresolvers import reverse
        return reverse('wcore:job_input', kwargs={'slug': self.slug})

    def duplicate_api_name(self, api_name):
        """ Check is another entity is set with same api_name
        :param api_name:
        """
        return self.__class__.objects.filter(api_name=api_name, job=self.job).exclude(pk=self.pk)


class JobOutputManager(models.Manager):
    """ JobInput model Manager """

    def get_by_natural_key(self, job, name):
        return self.get(job=job, _name=name)

    def create(self, **kwargs):
        sout = kwargs.pop('srv_output', None)
        if sout:
            kwargs.update(dict(_name=sout.name, type=sout.type))
        return super(JobOutputManager, self).create(**kwargs)

    @transaction.atomic
    def create_from_submission(self, job, submission_output, submitted_inputs):
        assert (isinstance(submission_output, SubmissionOutput))
        output_dict = dict(job=job, _name=submission_output.label, extension=submission_output.ext,
                           api_name=submission_output.api_name)
        if hasattr(submission_output, 'from_input') and submission_output.from_input:
            # issued from a input value
            from_input = submission_output.from_input
            logger.debug("Output issued from input %s[%s]", from_input.name, from_input.api_name)
            value_to_normalize = submitted_inputs.get(from_input.api_name, from_input.default)
            logger.debug('Value to normalize init 1 %s', value_to_normalize)
            if from_input.param_type == TYPE_FILE:
                logger.debug('From input is defined as a file')
                if type(value_to_normalize) is file or isinstance(value_to_normalize, File):
                    logger.debug('Value to normalize is a real file %s', value_to_normalize.name)
                    value_to_normalize = value_to_normalize.name
                elif isinstance(value_to_normalize, (str, unicode)):
                    logger.debug('Value to normalize is str %s', from_input.default)
                    value_to_normalize = from_input.default
            logger.debug("value to normalize %s", value_to_normalize)
            # input_value = normalize_value(value_to_normalize)
            input_value = value_to_normalize
            formatted_value = submission_output.file_pattern % input_value
            output_dict.update(dict(value=formatted_value))
        else:
            output_dict.update(dict(value=submission_output.file_pattern))
        return self.create(**output_dict)


class JobOutput(Ordered, Slugged, UrlMixin, ApiModel):
    """ JobOutput is association fro a Job, a SubmissionOutput, and the effective value set for this Job
    """

    class Meta:
        unique_together = ('api_name', 'job')

    objects = JobOutputManager()
    field_api_name = "value"
    #: Related :class:`waves.wcore.models.jobs.Job`
    job = models.ForeignKey(Job, related_name='outputs', on_delete=models.CASCADE)
    #: Related :class:`waves.wcore.models.services.SubmissionOutput`
    # srv_output = models.ForeignKey('SubmissionOutput', null=True, on_delete=models.CASCADE)
    #: Job Output value
    value = models.CharField('Output value', max_length=200, null=True, blank=True, default="")
    #: Each output may have its own identifier on remote adaptor
    remote_output_id = models.CharField('Remote output ID (on adaptor)', max_length=255, editable=False, null=True)
    _name = models.CharField('Name', max_length=50, null=False, blank=False, help_text='Output displayed name')
    extension = models.CharField('File extension', max_length=5, null=False, default="")

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

    def natural_key(self):
        return self.job.natural_key(), self._name

    def __str__(self):
        return '%s - %s' % (self.name, self.value)

    @property
    def file_name(self):
        base = self.value + self.extension
        if '.' not in base:
            return '.'.join([self.value, self.extension])
        return base

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
        from django.core.urlresolvers import reverse
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
