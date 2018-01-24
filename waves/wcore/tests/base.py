import json
import logging
import os
import random
import shutil
import time
from genericpath import isfile
from os.path import join, dirname, basename

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings, TestCase
from django.utils.timezone import localtime

from waves.wcore.adaptors import JobStatus
from waves.wcore.adaptors.loader import AdaptorLoader
from waves.wcore.models import get_service_model, get_submission_model, TextParam, BooleanParam, Job, JobInput, JobOutput, \
    Runner, AdaptorInitParam
from waves.wcore.models.const import ParamType
from waves.wcore.models.inputs import FileInput
from waves.wcore.models.services import ServiceRunParam
from waves.wcore.settings import waves_settings

Service = get_service_model()
Submission = get_submission_model()
User = get_user_model()
logger = logging.getLogger(__name__)


@override_settings(
    WAVES_CORE={
        'DATA_ROOT': join(settings.BASE_DIR, 'tests', 'data'),
        'JOB_BASE_DIR': join(settings.BASE_DIR, 'tests', 'data', 'jobs'),
        'BINARIES_DIR': join(settings.BASE_DIR, 'tests', 'data', 'bin'),
        'SAMPLE_DIR': join(settings.BASE_DIR, 'tests', 'data', 'sample'),
        'UPLOAD_MAX_SIZE': 20 * 1024 * 1024,
        'ADMIN_EMAIL': 'admin@test-waves.com',
        'ALLOW_JOB_SUBMISSION': True,
        'APP_NAME': 'WAVES',
        'JOBS_MAX_RETRY': 5,
        'JOB_LOG_LEVEL': logging.DEBUG,
        'SRV_IMPORT_LOG_LEVEL': logging.DEBUG,
        'KEEP_ANONYMOUS_JOBS': 30,
        'KEEP_REGISTERED_JOBS': 120,
        'NOTIFY_RESULTS': True,
        'REGISTRATION_ALLOWED': True,
        'SERVICES_EMAIL': 'service@test-waves.com',
        'TEMPLATE_PACK': getattr(settings, 'CRISPY_TEMPLATE_PACK', 'bootstrap3'),
        'SECRET_KEY': getattr(settings, 'SECRET_KEY', '')[0:32],
        'ADAPTORS_CLASSES': (
                'waves.wcore.adaptors.shell.SshShellAdaptor',
                'waves.wcore.adaptors.cluster.LocalClusterAdaptor',
                'waves.wcore.adaptors.shell.SshKeyShellAdaptor',
                'waves.wcore.adaptors.shell.LocalShellAdaptor',
                'waves.wcore.adaptors.cluster.SshClusterAdaptor',
                'waves.wcore.adaptors.cluster.SshKeyClusterAdaptor',
                'waves.wcore.adaptors.mocks.MockJobRunnerAdaptor'
        ),
        'TEMPLATES_PACKS': ['bootstrap3', 'bootstrap2'],
        'MAILER_CLASS': 'waves.wcore.mails.JobMailer',
    },
    MEDIA_ROOT=os.path.join(dirname(settings.BASE_DIR), 'tests', 'media'),
)
class BaseTestCase(TestCase):
    service = None
    services = []
    runners = []

    def setUp(self):
        super(BaseTestCase, self).setUp()
        super_user = User.objects.create(email='superadmin@waves.wcore.fr', username="superadmin", is_superuser=True)
        super_user.set_password('superadmin')
        super_user.save()
        admin_user = User.objects.create(email='admin@waves.wcore.fr', username="admin", is_staff=True)
        admin_user.set_password('admin')
        admin_user.save()
        api_user = User.objects.create(email="wavesapi@waves.wcore.fr", username="api_user", is_staff=False,
                                       is_superuser=False, is_active=True)
        api_user.set_password('api_user')
        api_user.save()
        self.users = {'api_user': api_user, 'admin': admin_user, 'superadmin': super_user}
        self.bootstrap_runners()

    def create_random_service(self, runner=None):
        service_runner = runner or self.runners[random.randint(0, len(self.runners) - 1)]
        service = Service.objects.create(name='Sample Service', runner=service_runner, status=3)
        service.default_submission.inputs.add(TextParam.objects.create(name='param1', default='Default1', submission=service.default_submission))
        service.default_submission.inputs.add(BooleanParam.objects.create(name='param2', default=False, submission=service.default_submission))
        service.default_submission.inputs.add(FileInput.objects.create(name='param3', submission=service.default_submission))
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
            logger.error(e.message)
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

    def test_overridden_config(self):
        from waves.wcore.settings import waves_settings
        self.assertEqual(waves_settings.JOB_BASE_DIR, join(settings.BASE_DIR, 'tests', 'data', 'jobs'))
        self.assertEqual(waves_settings.ADMIN_EMAIL, 'admin@test-waves.com')

    def bootstrap_runners(self):
        """ Create base models from all Current implementation parameters """
        self.runners = []
        loader = AdaptorLoader
        for adaptor in loader.get_adaptors():
            runner = Runner.objects.create(name="%s Runner" % adaptor.name,
                                           clazz='.'.join([adaptor.__module__, adaptor.__class__.__name__]))
            self.runners.append(runner)

        return self.runners

    def bootstrap_services(self):
        """ initialize a empty service for each defined runner """
        self.services = []
        i = 0
        for runner in self.bootstrap_runners():
            srv = Service.objects.create(name="Service %s" % runner.name, runner=runner,
                                         api_name="service_{}".format(i))
            i += 1
            self.services.append(srv)
        return self.services

    def create_test_file(self, path, index):
        full_path = join(waves_settings.DATA_ROOT, str(index) + '_' + path)
        f = open(full_path, 'w')
        f.write('sample content for input file %s' % (str(index) + '_' + path))
        f.close()
        f = open(full_path, 'rb')
        return f


class TestJobWorkflowMixin(TestCase):
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

    def create_cp_job(self, source_file, submission):
        job = self.create_base_job('Sample CP job', submission)
        shutil.copy(source_file, job.working_dir)
        job.inputs = [JobInput.objects.create(label="File To copy", name='source',
                                              value=basename(source_file), param_type=ParamType.TYPE_FILE, job=job),
                      JobInput.objects.create(label="Destination Dir", name="dest",
                                              value='dest_copy.txt', param_type=ParamType.TYPE_TEXT, job=job)]
        job.outputs = [JobOutput.objects.create(_name='Copied File', name='dest', value=job.inputs[1].value, job=job)]
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
            job.run_details()
            time.sleep(3)
            history = job.job_history.first()
            logger.debug("History timestamp %s", localtime(history.timestamp))
            logger.debug("Job status timestamp %s", job.status_time)
            self.assertTrue(job.results_available, "Job results are not available")
            for output_job in job.outputs.all():
                # TODO reactivate job output verification as soon as possible
                if not isfile(output_job.file_path):
                    logger.warning("Job <<%s>> did not output expected %s (test_data/jobs/%s/) ",
                                   job.title, output_job.value, job.slug)
                else:
                    logger.info("Expected output file found : %s ", output_job.file_path)
            self.assertTrue(job.status == JobStatus.JOB_TERMINATED)
            job.delete()
        else:
            logger.warning('problem with job status %s', job.get_status_display())

    def get_sample(self):
        from waves.wcore.settings import waves_settings
        return join(waves_settings.SAMPLE_DIR, 'test_copy.txt')

    def get_copy(self):
        return 'dest_copy.txt'

    def sample_runner(self, adaptor=None):
        """
        Return a new adaptor model instance from adaptor class object
        Args:
            adaptor: a JobRunnerAdaptor object
        Returns:
            Runner model instance
        """
        from waves.wcore.adaptors.mocks import MockJobRunnerAdaptor
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