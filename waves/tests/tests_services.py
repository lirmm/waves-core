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
import shutil
import time
from os.path import basename, join, isfile
from unittest import skip
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from waves.models import JobInput, JobOutput, Service, Job
from waves.core.const import ParamType, JobStatus

from tests.base import bootstrap_services, api_user, super_user, admin_user

logger = logging.getLogger(__name__)


class ServicesTestCase(TestCase):
    fixtures = ("accounts",
                "runners",
                # "services.json",
                # "copy_service.json"
                )

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
        if job.status in (JobStatus.JOB_COMPLETED, JobStatus.JOB_FINISHED):
            # Get job run details
            job.retrieve_run_details()
            time.sleep(3)
            history = job.job_history.first()
            logger.debug("History timestamp %s", time.localtime(history.timestamp))
            self.assertTrue(job.results_available, "Job results are not available")
            for output_job in job.outputs.all():
                # TODO reactivate job output verification as soon as possible
                if not isfile(output_job.file_path):
                    logger.warning("Job <<%s>> did not output expected %s (%s) ",
                                   job.title, output_job.value, output_job.file_path)
                    self.fail('Expected output not present')
                else:
                    logger.info("Expected output file found : %s ", output_job.file_path)
            self.assertTrue(job.status == JobStatus.JOB_FINISHED)
            self.assertEqual(job.exit_code, 0)
            job.delete()
        else:
            logger.warning('problem with job status %s', job.get_status_display())
            self.fail("Job failed")

    def _test_access(self, the_url, expected_status, user=None):
        self.client.login(username=user.username, password=user.username) if user else None
        the_response = self.client.get(the_url)
        self.assertEqual(the_response.status_code, expected_status,
                         "{} Status code {} [expected: {}]".format(the_url, the_response.status_code,
                                                                   expected_status))
        self.client.logout() if user else None

    def test_access_rules(self):
        services = bootstrap_services()
        self.assertGreater(len(services), 0)
        # List access => always 200
        response = self.client.get(reverse('wcore:services_list'))
        self.assertContains(response=response,
                            text="Sorry no service available online for now",
                            status_code=200)
        service = services[0]
        admin = admin_user()
        superadmin = super_user()
        api = api_user()
        # For draft Service is allowed only to creator and superadmin
        logger.debug('Test DRAFT status ...')
        service.status = service.SRV_DRAFT
        service.created_by = admin
        service.save()
        url = reverse('wcore:service_details', kwargs={'service_app_name': service.api_name})
        self._test_access(url, 403)
        self._test_access(url, 200, superadmin)
        self._test_access(url, 200, admin)
        self._test_access(url, 403, api)
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'service_app_name': service.api_name})
        self._test_access(url, 200, superadmin)
        self._test_access(url, 200, admin)
        self._test_access(url, 403)
        self._test_access(url, 403, api)
        logger.debug('Test DRAFT status OK')
        logger.debug('Test TEST status ...')
        service.status = service.SRV_TEST
        service.created_by = super_user()
        service.save()
        url = reverse('wcore:service_details', kwargs={'service_app_name': service.api_name})
        self._test_access(url, 403)
        self._test_access(url, 200, superadmin)
        self._test_access(url, 200, admin)
        self._test_access(url, 403, api)
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'service_app_name': service.api_name})
        self._test_access(url, 403)
        self._test_access(url, 200, superadmin)
        self._test_access(url, 200, admin)
        self._test_access(url, 403, api)
        logger.debug('Test TEST status OK')

        logger.debug('Test REGISTERED status ...')
        service.status = service.SRV_REGISTERED
        service.save()
        url = reverse('wcore:service_details', kwargs={'service_app_name': service.api_name})
        self._test_access(url, 403)
        self._test_access(url, 200, superadmin)
        self._test_access(url, 200, admin)
        self._test_access(url, 200, api)
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'service_app_name': service.api_name})
        self._test_access(url, 403)
        self._test_access(url, 200, superadmin)
        self._test_access(url, 200, admin)
        self._test_access(url, 200, api)
        logger.debug('Test REGISTERED status OK')

        logger.debug('Test RESTRICTED status ...')
        service.status = service.SRV_RESTRICTED
        service.save()
        url = reverse('wcore:service_details', kwargs={'service_app_name': service.api_name})
        url_service = reverse('wcore:service_details', kwargs={'service_app_name': service.api_name})
        self._test_access(url, 403)
        self._test_access(url, 200, superadmin)
        self._test_access(url, 200, admin)
        self._test_access(url, 403, api)

        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'service_app_name': service.api_name})
        self._test_access(url, 403)
        self._test_access(url, 200, superadmin)
        self._test_access(url, 200, admin)
        self._test_access(url, 403, api)
        # Add api_user to restricted client
        service.restricted_client.add(api)
        service.save()
        self._test_access(url_service, 200, api)
        self._test_access(url, 200, api)
        logger.debug('Test RESTRICTED status OK')
        logger.debug('Test PUBLIC status ...')
        service.status = service.SRV_PUBLIC
        service.save()
        url = reverse('wcore:service_details', kwargs={'service_app_name': service.api_name})
        self._test_access(url, 200)
        self._test_access(url, 200, superadmin)
        self._test_access(url, 200, admin)
        self._test_access(url, 200, api)
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'service_app_name': service.api_name})
        self._test_access(url, 200)
        self._test_access(url, 200, superadmin)
        self._test_access(url, 200, admin)
        self._test_access(url, 200, api)
        logger.debug('Test PUBLIC status OK')

    def create_cp_job(self, source_file, submission):
        job = self.create_base_job('Sample CP job', submission)
        shutil.copy(source_file, job.working_dir)
        job.inputs = [JobInput.objects.create(label="File To copy", name='source',
                                              value=basename(source_file), param_type=ParamType.TYPE_FILE, job=job),
                      JobInput.objects.create(label="Destination Dir", name="dest",
                                              value='dest_copy.txt', param_type=ParamType.TYPE_TEXT, job=job)]
        job.outputs = [JobOutput.objects.create(_name='Copied File', name='dest', value=job.inputs[1].value, job=job)]
        return job

    @skip('Not ready yet')
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
