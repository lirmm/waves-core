"""
Base Waves Unit Test class
"""
from __future__ import unicode_literals

import json
import logging
import os
import random
from os.path import dirname

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.test import override_settings, TestCase

from waves.wcore.models import get_service_model, Job, JobInput, JobOutput
from waves.wcore.tests.utils import get_sample_dir, create_runners

Service = get_service_model()

logger = logging.getLogger(__name__)


@override_settings(
    MEDIA_ROOT=os.path.join(dirname(settings.BASE_DIR), 'tests', 'media'),
    JOB_BASE_DIR=str(os.path.join(dirname(settings.BASE_DIR), 'tests', 'data', 'jobs')),
    DATA_ROOT=str(os.path.join(dirname(settings.BASE_DIR), 'tests', 'data')),
    SAMPLE_DIR=str(os.path.join(dirname(settings.BASE_DIR), 'tests', 'data', 'sample'))
)
class WavesBaseTestCase(TestCase):
    service = None

    def setUp(self):
        super(WavesBaseTestCase, self).setUp()
        self.runners = []
        for runner in create_runners():
            self.runners.append(runner)

    def _create_random_service(self):
        return Service.objects.create(name='Sample Service',
                                      runner=self.runners[random.randint(0, len(self.runners) - 1)])

    def _create_random_job(self):
        service = self._create_random_service()
        job = Job.objects.create(submission=service.default_submission,
                                 email_to='marc@fake.com')
        job.job_inputs.add(JobInput.objects.create(name="param1", value="Value1", job=job))
        job.job_inputs.add(JobInput.objects.create(name="param2", value="Value2", job=job))
        job.job_inputs.add(JobInput.objects.create(name="param3", value="Value3", job=job))
        job.outputs.add(JobOutput.objects.create(_name="out1", value="out1", job=job))
        job.outputs.add(JobOutput.objects.create(_name="out2", value="out2", job=job))
        return job

    def _loadServiceJobsParams(self, api_name):
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
        logger.debug('SubmissionSample dir %s %s', get_sample_dir(), self.service.api_name)
        with open(os.path.join(get_sample_dir(), self.service.api_name, 'runs.json'),
                  'r') as run_params:
            job_parameters = json.load(run_params)
        self.assertIsInstance(job_parameters, object)

        for job_params in job_parameters['runs']:
            logger.debug('job_params: %s %s ', job_params.__class__, job_params)
            submitted_input = {'title': job_params['title']}
            # All files inputs
            for key in job_params['inputs']:
                with open(os.path.join(get_sample_dir(), self.service.api_name,
                                       job_params['inputs'][key])) as f:
                    submitted_input.update({key: f.read()})
                    # self.service.default_submission.inputs.add(SubmissionParam.objects.create(ser))
            for key in job_params['params']:
                submitted_input.update({key: job_params['params'][key]})
            jobs_submitted_input.append(submitted_input)
        return jobs_submitted_input
