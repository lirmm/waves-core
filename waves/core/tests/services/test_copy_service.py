import shutil
import logging
from os.path import basename, join

from django.conf import settings
from django.test import TestCase

from waves.core.models import JobInput, JobOutput, Job
from waves.core.models import Service
from waves.core.models.const import ParamType
from waves.core.tests.base import WavesTestCaseMixin, TestJobWorkflowMixin

logger = logging.getLogger(__name__)


class CopyServiceTestCase(TestCase, WavesTestCaseMixin, TestJobWorkflowMixin):
    fixtures = ['waves/core/tests/fixtures/accounts.json', 'waves/core/tests/fixtures/runners.json',
                'waves/core/tests/fixtures/copy_service.json']

    def create_cp_job(self, source_file, submission):
        job = self.create_base_job('Sample CP job', submission)
        shutil.copy(source_file, job.working_dir)
        job.inputs = [JobInput.objects.create(label="File To copy", name='source',
                                              value=basename(source_file), param_type=ParamType.TYPE_FILE, job=job),
                      JobInput.objects.create(label="Destination Dir", name="dest",
                                              value='dest_copy.txt', param_type=ParamType.TYPE_TEXT, job=job)]
        job.outputs = [JobOutput.objects.create(_name='Copied File', name='dest', value=job.inputs[1].value, job=job)]
        return job

    def test_local_cp_job(self):
        cp_service = Service.objects.filter(api_name='copy').first()
        with open(join(settings.WAVES_CORE['DATA_ROOT'], "test.fasta"), 'rb') as fp:
            job_payload = {
                'src': fp.read(),
                'dest': 'test_fasta_copy.txt'
            }
        logger.debug('Service runner "%s"', cp_service.get_runner().name)
        job = Job.objects.create_from_submission(cp_service.default_submission, job_payload)
        logger.info('job command line %s ', job.command_line)
        self.run_job_workflow(job)
