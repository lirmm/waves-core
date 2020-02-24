import json
import logging
from os.path import join

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from waves.core.models import Service, Submission, Job, JobInput, \
    Runner, AdaptorInitParam
from waves.core.models import ServiceRunParam
from waves.core.settings import waves_settings

logger = logging.getLogger(__name__)


class WavesTestCaseMixin:

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

    def get_test_file(self):
        from waves.core.settings import waves_settings
        return open(join(waves_settings.DATA_ROOT, "test.fasta"), 'rb')


class TestJobWorkflowMixin(object):
    jobs = []

    @staticmethod
    def service_sample_dir(service_api_name):
        return join(waves_settings.SAMPLE_DIR, service_api_name)

    @staticmethod
    def create_base_job(title="Sample Copy Job -- Test", submission=None):
        job = Job.objects.create(title=title, submission=submission)
        return job

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
        from waves.core.tests.mocks import MockJobRunnerAdaptor
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


