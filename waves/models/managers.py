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
from os import path as path

from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models, transaction
from django.db.models import Q
from psutil import long

from waves.core.const import JobStatus, ParamType
from waves.core.exceptions import JobMissingMandatoryParam

logger = logging.getLogger(__name__)


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
        Specific query set to filter only :class:`waves.core.models.jobs.JobAdminHistory` objects

        :return: QuerySet
        """
        return super(JobAdminHistoryManager, self).get_queryset().filter(is_admin=True)

    def create(self, **kwargs):
        """ Force 'is_admin' flag for JobAdminHistory models objects

        :return: a JobAdminHistory object
        """
        kwargs.update({'is_admin': True})
        return super(JobAdminHistoryManager, self).create(**kwargs)


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

            - User is a super_user, return all jobs
            - User is member of staff (access to Django admin): returns only jobs from services user has created,
                jobs created by user, or where associated email is its email
            - User is simply registered on website, returns only those created by its own

        :param user: current user (may be Anonymous)
        :return: QuerySet
        """
        if not user or user.is_anonymous:
            return self.none()
        if user.is_superuser:
            return self.all()
        return self.filter(Q(client=user) | Q(email_to=user.email))

    def get_service_job(self, user, service):
        """
        Returns jobs filtered by service, according to following access rule:
        * user is simply registered, return its jobs, filtered by service
        :param user: currently logged in user
        :param service: service model object to filter
        :return: QuerySet
        """
        return self.get_user_job(user).filter(submission__service__in=[service, ])

    def get_submission_job(self, user, submission):
        """
        Returns jobs filtered by service, according to following access rule:
        * user is simply registered, return its jobs, filtered by service
        :param user: currently logged in user
        :param submission: submission model object to filter
        :return: QuerySet
        """
        return self.get_user_job(user).filter(submission=submission)

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
                    JobStatus.JOB_CREATED,
                    JobStatus.JOB_PREPARED,
                    JobStatus.JOB_QUEUED,
                    JobStatus.JOB_RUNNING))
            # get only user jobs
            return self.filter(_status__in=(JobStatus.JOB_CREATED,
                                            JobStatus.JOB_PREPARED,
                                            JobStatus.JOB_QUEUED,
                                            JobStatus.JOB_RUNNING),
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
            self.filter(status=JobStatus.JOB_CREATED,
                        client=user,
                        **extra_filter).order_by('-created')
        return self.filter(_status=JobStatus.JOB_CREATED,
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
        from waves.models import JobInput, JobOutput
        default_email = user.email if user and not user.is_anonymous else None
        follow_email = email_to or default_email
        client = user if user and not user.is_anonymous else None
        mandatory_params = submission.expected_inputs.filter(required=True)
        missing = {m.name: '%s (:%s:) is required field' % (m.label, m.api_name) for m in mandatory_params if
                   m.api_name not in submitted_inputs.keys()}
        if len(missing) > 0:
            logger.warning("Received keys %s", submitted_inputs.keys())
            logger.warning("Expected mandatory %s", [(m.label, m.api_name) for m in mandatory_params])
            logger.warning("Missing %s", [m for m in missing])
            raise ValidationError(missing)
        if update is None:
            job = self.create(email_to=follow_email,
                              client=client,
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

        # First create inputs
        submission_inputs = submission.inputs.filter(api_name__in=submitted_inputs.keys()).exclude(required=None)
        for service_input in submission_inputs:
            incoming_input = submitted_inputs.get(service_input.api_name, None)
            # test service input mandatory, without default and no value
            if service_input.required and not service_input.default and incoming_input is None:
                raise JobMissingMandatoryParam(service_input.label, job)
            logger.debug("Current Service Input: %s, %s", service_input, service_input.required)
            job.logger.debug('Param %s', service_input.api_name)
            logger.debug('Param %s', service_input.api_name)
            job.save()
            if incoming_input:
                # transform single incoming into list
                incoming_input = [incoming_input] if type(incoming_input) is not list else incoming_input
                for in_input in incoming_input:
                    logger.debug('Adding Job Input %s %s %s %s', job, service_input, service_input.order, in_input)
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
            logger.debug('%s %s', job.command, job.command_line_arguments)
            logger.debug('Expected outputs will be:')
            for j_output in job.outputs.all():
                logger.debug('Output %s: %s', j_output.name, j_output.value)
                logger.debug('Output %s: %s', j_output.name, j_output.value)
        job._command_line = "{} {}".format(job.command, job.command_line_arguments)
        if force_status is not None and force_status in JobStatus.STATUS_MAP.keys():
            job.status = force_status
        job.save()
        return job


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
        """ Create Job Input from submitted data

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
        if service_input.param_type == ParamType.TYPE_FILE:
            if isinstance(submitted_input, File):
                # classic uploaded file
                filename = path.join(job.working_dir, submitted_input.name)
                with open(filename, 'wb+') as uploaded_file:
                    for chunk in submitted_input.chunks():
                        uploaded_file.write(chunk)
                        # input_dict.update(dict(value='inputs/' + submitted_input.name))
            elif isinstance(submitted_input, (int, long)):
                # Manage sample data
                input_sample = FileInputSampleManager.get(pk=submitted_input)
                filename = path.join(job.working_dir, path.basename(input_sample.file.name))
                # input_dict['command_type'] = input_sample.file_input.cmd_format
                input_dict['value'] = path.basename(input_sample.file.name)
                with open(filename, 'wb+') as uploaded_file:
                    for chunk in input_sample.file.chunks():
                        uploaded_file.write(chunk)
            elif isinstance(submitted_input, str):
                # copy / paste content
                if service_input.default:
                    filename = path.join(job.working_dir, service_input.default)
                    input_dict.update(dict(value=service_input.default))
                else:
                    filename = path.join(job.working_dir, service_input.name + '.txt')
                    input_dict.update(dict(value=service_input.name + '.txt'))
                with open(filename, 'wb+') as uploaded_file:
                    # TODO test this
                    uploaded_file.write(submitted_input.encode())
            else:
                logger.warning(
                    "Unable to determine usable type for input %s:%s " % (service_input.name, submitted_input))
        new_input = self.create(**input_dict)
        return new_input


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
        """ Create job expected output from submission data """
        output_dict = dict(job=job, _name=submission_output.label, extension=submission_output.extension,
                           api_name=submission_output.api_name)
        if hasattr(submission_output, 'from_input') and submission_output.from_input:
            # issued from a input value
            from_input = submission_output.from_input
            logger.debug("Output issued from input %s[%s]", from_input.name, from_input.api_name)
            value_to_normalize = submitted_inputs.get(from_input.api_name, from_input.default)
            logger.debug('Value to normalize init 1 %s', value_to_normalize)
            if from_input.param_type == ParamType.TYPE_FILE:
                logger.debug('From input is defined as a file')
                if isinstance(value_to_normalize, File):
                    logger.debug('Value to normalize is a real file %s', value_to_normalize.name)
                    value_to_normalize = value_to_normalize.name
                elif isinstance(value_to_normalize, str):
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

        if not user.is_anonymous:
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


class FileInputSampleManager(models.Manager):
    pass
