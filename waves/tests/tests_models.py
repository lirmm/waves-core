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
import random
from os.path import join, abspath, dirname, isdir, isfile

from django.test import TestCase, override_settings
from django.utils.module_loading import import_string

from core.const import JobStatus
from waves.core.adaptors import JobAdaptor
from waves.models import Service, Submission
from .base import bootstrap_runners, bootstrap_services, api_user, simple_job

logger = logging.getLogger(__name__)


@override_settings(
    WAVES_CORE={
        'JOB_BASE_DIR': join(dirname(dirname(abspath(__file__))), 'tests', 'data', 'jobs'),
        'ADMIN_EMAIL': 'admin@test-waves.com'
    }
)
class WavesModelsTestCase(TestCase):
    fixtures = ("accounts.json",)
    services = []
    runners = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.services = bootstrap_services()
        cls.runners = bootstrap_runners()

    def test_create_runner(self):
        for runner in self.runners:
            logger.info('Current: %s - %s', runner.name, runner.clazz)
            adaptor = runner.adaptor
            self.assertIsInstance(adaptor, JobAdaptor)
            self.assertListEqual(sorted(runner.run_params.keys()), sorted(adaptor.init_params.keys()))
            obj_runner = import_string(runner.clazz)
            expected_params = obj_runner().init_params
            runner_params = adaptor.init_params
            logger.debug("Expected %s", expected_params)
            logger.debug("Defaults %s", runner_params)
            logger.debug("Config %s", adaptor.dump_config())
            self.assertEquals(sorted(expected_params), sorted(runner_params))

    def test_runs_relationship(self):
        self.fail("testing generated reverse relationship naming ")

    def test_create_service(self):
        self.assertGreater(len(self.services), 0)
        for service in self.services:
            self.assertEqual(service.submissions.count(), 1)
            # Assert that service params has a length corresponding to 'allowed override' value
            self.assertListEqual(sorted(service.run_params.keys()), sorted(service.runner.run_params.keys()))
            self.assertIsNotNone(service.api_name)
            self.assertEqual(service.status, Service.SRV_DRAFT)
            logger.debug('Service %s', service.api_name)

    def test_services_signals(self):
        service = Service(name="Service", runner=random.choice(self.runners))
        service.save()
        self.assertEqual(service.submissions.count(), 1)
        logger.debug('Service Default submission has been created - service_post_save_handler')
        service.submissions.add(Submission.objects.create(service=service))
        service.save()
        self.assertEqual(service.submissions.count(), 2)
        self.assertIsNotNone(service.submissions.filter(name='sub_' + service.name).first())
        # service_post_save_handler
        logger.debug('Service submission name has been set - submission_pre_save_handler')
        # submission_pre_save_handler
        self.assertEqual(service.default_submission.name, 'default')
        # submission_post_save_handler
        self.assertEqual(service.default_submission.exit_codes.count(), 2)
        logger.debug('Service submission have two defaults exit codes - submission_post_save_handler')
        self.assertTrue(isdir(service.sample_dir))
        service.delete()
        # service_post_delete_handler
        self.assertFalse(isdir(service.sample_dir))
        logger.debug('Service Sample directory has been deleted - service_post_delete_handler')

    def test_runner_signals(self):
        runner = random.choice
        # runner_post_save_handler

        # adaptor_mixin_post_save_handler
        # adaptor_param_pre_save_handler

    def test_jobs_signals(self):
        job = simple_job(random.choice(self.services), api_user())
        # job_pre_save_handler
        self.assertRegexpMatches(job.title, r'Job \[[A-Z0-9]+\]')
        job.logger.debug("Test Debug Log message")
        # job_post_save_handler (create)
        self.assertTrue(isdir(job.working_dir))
        self.assertTrue(isfile(join(job.working_dir, job.stdout)))
        self.assertTrue(isfile(join(job.working_dir, job.stderr)))
        self.assertTrue(isfile(join(job.working_dir, job.log_file)))
        self.assertEqual(job.status, JobStatus.JOB_CREATED)
        [self.assertIsNotNone(i.api_name) for i in job.job_inputs.all()]
        [self.assertIsNotNone(i.api_name) for i in job.outputs.all()]
        logger.debug('Job directories/files have been created - job_post_save_handler')
        self.assertEqual(job.job_history.count(), 1)
        job.message = "Another job message"
        job.status = JobStatus.JOB_PREPARED
        job.save()
        self.assertEqual(job.job_history.count(), 2)
        work_dir = job.working_dir
        job.delete()
        # job_post_delete_handler (delete)
        self.assertFalse(isdir(work_dir))
        logger.debug('Job directories has been deleted - job_post_delete_handler')
