from django.contrib.auth import get_user_model

from waves.core.adaptors.loader import AdaptorLoader
from waves.core.models import Runner, Service, TextParam, BooleanParam, FileInput, Job, JobInput, JobOutput, SubmissionOutput

User = get_user_model()


def bootstrap_runners():
    """ Create base models from all Current implementation parameters """
    loader = AdaptorLoader
    runners = []
    for adaptor in loader.get_adaptors():
        runner = Runner.objects.create(name="%s Runner" % adaptor.name,
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


def sample_service(runner):
    service_runner = runner
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


def sample_job(service, user):
    job_service = service
    job = Job.objects.create(submission=job_service.default_submission,
                             client=user,
                             email_to='marc@fake.com')
    job.job_inputs.add(JobInput.objects.create(name="param1", value="Value1", job=job))
    job.job_inputs.add(JobInput.objects.create(name="param2", value="Value2.txt", job=job))
    job.job_inputs.add(JobInput.objects.create(name="param3", value="Value3", job=job))
    job.outputs.add(JobOutput.objects.create(_name="out1", value="out1", job=job))
    job.outputs.add(JobOutput.objects.create(_name="out2", value="out2", job=job))
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
