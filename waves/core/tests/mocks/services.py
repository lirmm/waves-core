from waves.core.models import *
from waves.core.tests.mocks import MockJobRunnerAdaptor


class SampleService(object):

    def __init__(self) -> None:
        super().__init__()
        adaptor = MockJobRunnerAdaptor()
        print("Names", adaptor.class_name)
        runner = Runner.objects.create(name="MockRunner",
                                       enabled=True,
                                       description="Mock Runner",
                                       short_description="Mock Runner",
                                       clazz=adaptor.class_name)
        self.service = Service.objects.create(name='Sample Service',
                                              runner=runner,
                                              status=Service.SRV_PUBLIC)
        print(self.service.default_submission)

    def simple_params(self):
        self.service.default_submission.inputs.add(
            TextParam.objects.create(name='TextInput',
                                     default='default',
                                     submission=self.service.default_submission))
        self.service.default_submission.inputs.add(
            BooleanParam.objects.create(name='BooleanParam',
                                        default=False,
                                        submission=self.service.default_submission))
        self.service.default_submission.inputs.add(
            FileInput.objects.create(name='FileInputParam',
                                     submission=self.service.default_submission))
        self.service.default_submission.outputs.add(
            SubmissionOutput.objects.create(submission=self.service.default_submission,
                                            label="Sample Output 1",
                                            extension="txt")
        )
        self.service.default_submission.outputs.add(
            SubmissionOutput.objects.create(submission=self.service.default_submission,
                                            label="Sample Output 2",
                                            extension="fasta")
        )

    def create_simple_job(self, user=None):
        job = Job.objects.create(submission=self.service.default_submission,
                                 client=user,
                                 email_to='waves@waves.com')
        for param in self.service.default_submission.inputs:
            job.job_inputs.add(JobInput.objects.create(name=f"Input_{param.name}",
                                                       value=f"Value_{param.name}",
                                                       job=job))
        for out in self.service.default_submission.outputs:
            job.outputs.add(JobOutput.objects.create(name=f"out {out.name}",
                                                     value=f"out value {out.name}",
                                                     job=job))
        return job
