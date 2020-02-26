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
from os.path import join

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from waves.core.loader import AdaptorLoader
from waves.models import TextParam, BooleanParam, SubmissionOutput, Service, Job, JobInput, Runner,\
    AdaptorInitParam
from waves.settings import waves_settings

logger = logging.getLogger(__name__)


class WavesTestCaseMixin(TestCase):
    jobs = []

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
        from waves.settings import waves_settings
        return open(join(waves_settings.DATA_ROOT, "test.fasta"), 'rb')


def sample_runner(adaptor=None):
    """
    Return a new adapter model instance from adapter class object
    Returns:
        Runner model instance
        :param adaptor:
    """
    from tests.mocks import MockJobRunnerAdaptor
    impl = adaptor or MockJobRunnerAdaptor()
    runner_model = Runner.objects.create(name=impl.__class__.__name__,
                                         description='SubmissionSample Runner %s' % impl.__class__.__name__,
                                         clazz='%s.%s' % (impl.__module__, impl.__class__.__name__))
    object_ctype = ContentType.objects.get_for_model(runner_model)
    for name, value in impl.init_params.items():
        AdaptorInitParam.objects.update_or_create(name=name, content_type=object_ctype, object_id=runner_model.pk,
                                                  defaults={'value': value})
    return runner_model


def sample_job(service, user=None):
    """
    Return a sample faked Job instance for service
    :param service: a Service model instance
    :param user: a auth.User Object
    :return waves.models.Job
    """
    job = Job.objects.create(title='SubmissionSample Job',
                             submission=service.submissions.first(),
                             user=user)
    srv_submission = service.default_submission

    for srv_input in srv_submission.inputs.all():
        job.job_inputs.add(JobInput.objects.create(srv_input=srv_input, job=job, value="fake_value"))
    return job


def get_copy():
    return 'dest_copy.txt'


def service_sample_dir(service_api_name):
    return join(waves_settings.SAMPLE_DIR, service_api_name)


def create_base_job(title="Sample Copy Job -- Test", submission=None):
    job = Job.objects.create(title=title, submission=submission)
    return job


def get_sample():
    from waves.settings import waves_settings
    return join(waves_settings.SAMPLE_DIR, 'test_copy.txt')


User = get_user_model()


def bootstrap_runners():
    """ Create base models from all Current implementation parameters """
    loader = AdaptorLoader
    runners = []
    for adaptor in loader.get_adaptors():
        runner = Runner.objects.create(name="%s" % adaptor.name,
                                       clazz='.'.join([adaptor.__module__, adaptor.__class__.__name__]))
        runners.append(runner)
    return runners


def bootstrap_services():
    """ initialize a empty service for each defined runner """
    services = []
    for runner in bootstrap_runners():
        srv = Service.objects.create(name="Service %s" % runner.name,
                                     runner=runner)
        srv.default_submission.inputs.add(
            TextParam.objects.create(name='param1', default='Default1', submission=srv.default_submission))
        srv.default_submission.inputs.add(
            BooleanParam.objects.create(name='param2', default=False, submission=srv.default_submission))
        srv.default_submission.outputs.add(
            SubmissionOutput.objects.create(label='Output 1',
                                            name='output1',
                                            submission=srv.default_submission,
                                            extension='txt'))
        services.append(srv)
    return services


def sample_service(runner=None):
    service_runner = runner or bootstrap_runners()[0]
    service = Service.objects.create(name='Sample Service', runner=service_runner, status=3)
    service.default_submission.inputs.add(
        TextParam.objects.create(name='param1',
                                 default='Default1',
                                 submission=service.default_submission,
                                 order=1))
    service.default_submission.inputs.add(
        BooleanParam.objects.create(name='param2',
                                    default=False,
                                    submission=service.default_submission,
                                    order=2))
    return service


def api_user():
    return User.objects.get(username='wavesapi')


def super_user():
    return User.objects.get(username='superadmin')


def admin_user():
    return User.objects.get(username='admin')


def simple_job(service, user=None):
    job = Job.objects.create(submission=service.default_submission,
                             client=user,
                             email_to='waves@waves.com')
    job.job_inputs.add(JobInput.objects.create(name='param1', value="Text Value", job=job))
    job.job_inputs.add(JobInput.objects.create(name='param2', value=False, job=job))
    return job