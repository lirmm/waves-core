import json
import logging
import time
from genericpath import isfile
from os.path import join

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import localtime

from waves.core.adaptors.const import JobStatus
from waves.core.models import Service, Submission, TextParam, BooleanParam, Job, JobInput, \
    JobOutput, Runner, AdaptorInitParam
from waves.core.models.inputs import FileInput
from waves.core.models import ServiceRunParam
from waves.core.settings import waves_settings
from waves.core.tests.mocks import MockJobRunnerAdaptor

User = get_user_model()
logger = logging.getLogger(__name__)


class WavesTestCaseMixin(object):
    service = None
    services = []
    runner = MockJobRunnerAdaptor

    def __init__(self):
        super_user = User.objects.create(email='superadmin@waves.core.fr',
                                         username="superadmin",
                                         is_superuser=True)
        super_user.set_password('superadmin')
        super_user.save()
        admin_user = User.objects.create(email='admin@waves.core.fr', username="admin", is_staff=True)
        admin_user.set_password('admin')
        admin_user.save()
        api_user = User.objects.create(email="wavesapi@waves.core.fr", username="api_user", is_staff=False,
                                       is_superuser=False, is_active=True)
        api_user.set_password('api_user')
        api_user.save()
        self.users = {'api_user': api_user, 'admin': admin_user, 'superadmin': super_user}

    @property
    def api_user(self):
        return self.users['api_user']

    @property
    def super_user(self):
        return self.users['superadmin']

    @property
    def admin_user(self):
        return self.users['admin']

    def create_random_service(self, runner=None):
        service_runner = self.runner  # self.runners[random.randint(0, len(self.runners) - 1)]
        service = Service.objects.create(name='Sample Service', runner=service_runner, status=3)
        service.default_submission.inputs.add(
            TextParam.objects.create(name='param1', default='Default1', submission=service.default_submission))
        service.default_submission.inputs.add(
            BooleanParam.objects.create(name='param2', default=False, submission=service.default_submission))
        service.default_submission.inputs.add(
            FileInput.objects.create(name='param3', submission=service.default_submission))
        return service

    def create_random_job(self, service=None, runner=None, user=None):
        job_service = service or self.create_random_service(runner)
        job = Job.objects.create(submission=job_service.default_submission,
                                 client=user,
                                 email_to='marc@fake.com')
        job.job_inputs.add(JobInput.objects.create(name="param1", value="Value1", job=job))
        job.job_inputs.add(JobInput.objects.create(name="param2", value="Value2.txt", job=job))
        job.job_inputs.add(JobInput.objects.create(name="param3", value="Value3", job=job))
        job.outputs.add(JobOutput.objects.create(_name="out1", value="out1", job=job))
        job.outputs.add(JobOutput.objects.create(_name="out2", value="out2", job=job))
        return job

    def load_service_jobs_params(self, api_name):
        """
        Test specific phyisic_ist job submission
        Returns:
        """
        jobs_submitted_input = []
        try:
            self.service = Service.objects.get(api_name=api_name)
        except ObjectDoesNotExist as e:
            logger.error(e)
            # self.skipTest("No physic_ist service available")
            if self.service is None:
                self.service = Service.objects.create(name=api_name, api_name=api_name)
            self.service.api_name = api_name
            self.service.save()
        logger.debug('Physic_IST service %s %s ', self.service.name, self.service.version)
        logger.debug('SubmissionSample dir %s %s', self.service_sample_dir(self.service.api_name))
        with open(join(self.service_sample_dir(self.service.api_name), 'runs.json'), 'r') as run_params:
            job_parameters = json.load(run_params)

        self.assertIsInstance(job_parameters, json)

        for job_params in job_parameters['runs']:
            logger.debug('job_params: %s %s ', job_params.__class__, job_params)
            submitted_input = {'title': job_params['title']}
            # All files inputs
            for key in job_params['inputs']:
                with open(join(self.service_sample_dir(self.service.api_name), job_params['inputs'][key])) as f:
                    submitted_input.update({key: f.read()})
                    # self.service.default_submission.inputs.add(SubmissionParam.objects.create(ser))
            for key in job_params['params']:
                submitted_input.update({key: job_params['params'][key]})
            jobs_submitted_input.append(submitted_input)
        return jobs_submitted_input

    def login(self, username):
        self.assertTrue(self.client.login(username=self.users[username], password=self.users[username]))
        return self.users[username]

    def logout(self):
        return self.client.logout()

    def get_test_file(self):
        from waves.core.settings import waves_settings
        return open(join(waves_settings.DATA_ROOT, "test.fasta"), 'rb')


class TestJobWorkflowMixin(object):
    jobs = []

    def tearDown(self):
        super(TestJobWorkflowMixin, self).tearDown()

    @staticmethod
    def service_sample_dir(service_api_name):
        return join(waves_settings.SAMPLE_DIR, service_api_name)

    @staticmethod
    def create_base_job(title="Sample Empty Job -- Test", submission=None):
        job = Job.objects.create(title=title, submission=submission)
        return job

    def run_job_workflow(self, job):
        """ Run a full complete job workflow, you should call this method catching "AssertionError" to get
        error messages in your tests
        """
        logger.info('Starting workflow process for job %s', job)
        self.assertTrue(job.job_history.count() == 1,
                        "Wrong job history count %s (expected 1)" % job.job_history.count())
        job.run_prepare()
        time.sleep(3)
        self.assertTrue(job.status == JobStatus.JOB_PREPARED,
                        "Wrong job status %s (expected %s) " % (job.status, JobStatus.JOB_PREPARED))
        job.run_launch()
        time.sleep(3)
        logger.debug('Remote Job ID %s', job.remote_job_id)
        self.assertTrue(job.status == JobStatus.JOB_QUEUED,
                        "Wrong job status %s (expected %s) " % (job.status, JobStatus.JOB_QUEUED))
        for ix in range(100):
            job_state = job.run_status()
            logger.info(u'Current job state (%i) : %s ', ix, job.get_status_display())
            if job_state >= JobStatus.JOB_COMPLETED:
                logger.info('Job state ended to %s ', job.get_status_display())
                break
            time.sleep(3)
        if job.status in (JobStatus.JOB_COMPLETED, JobStatus.JOB_TERMINATED):
            # Get job run details
            job.retrieve_run_details()
            time.sleep(3)
            history = job.job_history.first()
            logger.debug("History timestamp %s", localtime(history.timestamp))
            self.assertTrue(job.results_available, "Job results are not available")
            for output_job in job.outputs.all():
                # TODO reactivate job output verification as soon as possible
                if not isfile(output_job.file_path):
                    logger.warning("Job <<%s>> did not output expected %s (%s) ",
                                   job.title, output_job.value, output_job.file_path)
                    self.fail('Expected output not present')
                else:
                    logger.info("Expected output file found : %s ", output_job.file_path)
            self.assertTrue(job.status == JobStatus.JOB_TERMINATED)
            self.assertEqual(job.exit_code, 0)
            job.delete()
        else:
            logger.warning('problem with job status %s', job.get_status_display())
            self.fail("Job failed")

    def get_sample(self):
        from waves.core.settings import waves_settings
        return join(waves_settings.SAMPLE_DIR, 'test_copy.txt')

    def get_copy(self):
        return 'dest_copy.txt'

    def sample_runner(self, adaptor=None):
        """
        Return a new adapter model instance from adapter class object
        Returns:
            Runner model instance
            :param adaptor:
        """
        from core import MockJobRunnerAdaptor
        impl = adaptor or MockJobRunnerAdaptor()
        runner_model = Runner.objects.create(name=impl.__class__.__name__,
                                             description='SubmissionSample Runner %s' % impl.__class__.__name__,
                                             clazz='%s.%s' % (impl.__module__, impl.__class__.__name__))
        object_ctype = ContentType.objects.get_for_model(runner_model)
        for name, value in impl.init_params.items():
            AdaptorInitParam.objects.update_or_create(name=name, content_type=object_ctype, object_id=runner_model.pk,
                                                      defaults={'value': value})
        return runner_model

    def sample_job(self, service):
        """
        Return a new Job model instance for service
        Args:
            service: a Service model instance
        Returns:
            Job model instance
        """

        job = Job.objects.create(title='SubmissionSample Job', submission=service.submissions.first())
        srv_submission = service.default_submission
        for srv_input in srv_submission.inputs.all():
            job.job_inputs.add(JobInput.objects.create(srv_input=srv_input, job=job, value="fake_value"))
        return job

    def sample_service(self, runner=None, init_params=None):
        """ Create a sample service for this runner """
        i_runner = runner or self.sample_runner()
        service = Service.objects.create(name='Sample Service', runner=i_runner)
        if init_params:
            for name, value in init_params:
                service.run_params.add(ServiceRunParam.objects.update_or_create(name=name, value=value))
        sub = Submission.objects.create(name="Default Submission", service=service)
        service.submissions.add(sub)

        return service
