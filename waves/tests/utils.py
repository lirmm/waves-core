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
from django.contrib.auth import get_user_model

from waves.core.loader import AdaptorLoader
from waves.models import Runner, Service, TextParam, BooleanParam, Job, JobInput, JobOutput, SubmissionOutput

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


def sample_job(service=None, user=None):
    job_service = service or bootstrap_services()[0]
    job = Job.objects.create(submission=job_service.default_submission,
                             client=user,
                             email_to='user@fake.com')
    for param in service.default_submission.inputs.all():
        job.job_inputs.add(JobInput.objects.create(name=param.api_name, value="Value", job=job))
    for param in service.default_submission.outputs.all():
        job.outputs.add(JobOutput.objects.create(_name=param.api_name, value="out Value", job=job))
    return job


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
