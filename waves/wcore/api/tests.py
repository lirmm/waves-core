from __future__ import unicode_literals

import logging
from urlparse import urlparse

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

import waves.wcore.adaptors.const
from waves.wcore.models.const import *
from waves.wcore.models import Job, get_service_model, Runner
from waves.wcore.models.inputs import AParam
from waves.wcore.tests import BaseTestCase
from waves.wcore.models.const import *

Service = get_service_model()

logger = logging.getLogger(__name__)


class BaseAPITestCase(APITestCase, BaseTestCase):
    fixtures = ['waves/wcore/tests/fixtures/users.json', 'waves/wcore/tests/fixtures/services.json']


class WavesAPIV1TestCase(BaseAPITestCase):
    def test_api_root(self):
        api_root = self.client.get(reverse('wapi:api_v1:api-root'))
        self.assertEqual(api_root.status_code, status.HTTP_200_OK)
        logger.debug('Results: %s ', api_root.data)
        self.assertIn('services', api_root.data.keys())
        self.assertIn('jobs', api_root.data.keys())
        tool_list = self.client.get(api_root.data['services'], format='json')
        self.assertIsNotNone(tool_list.data)
        logger.debug('Tools list length %s' % len(tool_list.data))
        logger.debug(tool_list.data)
        for service in tool_list.data:
            self.assertIn('url', service.keys())
            logger.debug('ServiceTool url: %s', service['url'])
            tool_details = self.client.get(service['url'], format='json')
            logger.debug('ServiceTool: %s', tool_details.data['name'])
            self.assertIsNotNone(tool_details.data['default_submission_uri'])

    def test_http_methods(self):
        # TODO test authorization
        pass

    def test_create_job_api(self):
        """
        Ensure for any service, we can create a job according to retrieved parameters
        """
        import random
        import string
        logger.debug('Retrieving service-list from ' + reverse('wapi:api_v2:waves-services-list'))
        logger.debug('1 %s service loaded ' % Service.objects.count())
        expected_jobs = 0
        for service in Service.objects.all():
            logger.debug("'%s' (%s) is available with %s submission(s)" % (
                service.name, service.get_status_display(), service.submissions_api.count()))
            expected_jobs += service.submissions_api.count()
        tool_list = self.client.get(reverse('wapi:api_v1:waves-services-list'), format="json")
        self.assertEqual(tool_list.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(tool_list)
        logger.debug(tool_list.data)
        for servicetool in tool_list.data:
            logger.debug('Creating job submission for %s %s', servicetool['name'], str(servicetool['version']))
            # for each servicetool retrieve inputs
            self.assertIsNotNone(servicetool['url'])
            detail = self.client.get(servicetool['url'])
            # logger.debug('Details data: %s', detail)
            tool_data = detail.data
            self.assertTrue('submissions' in tool_data)
            i = 0
            input_datas = {}
            submissions = tool_data.get('submissions')
            logger.debug(submissions)
            for submission in submissions:
                for job_input in submission['inputs']:
                    if job_input['type'] == TYPE_FILE:
                        i += 1
                        input_data = self.create_test_file(job_input['name'], i)
                        logger.debug('file input %s', input_data)
                    elif job_input['type'] == TYPE_INT:
                        input_data = int(random.randint(0, 199))
                        logger.debug('number input%s', input_data)
                    elif job_input['type'] == TYPE_DECIMAL:
                        input_data = int(random.randint(0, 199))
                        logger.debug('number input%s', input_data)
                    elif job_input['type'] == TYPE_BOOLEAN:
                        input_data = random.randrange(100) < 50
                    elif job_input['type'] == TYPE_TEXT:
                        input_data = ''.join(random.sample(string.letters, 15))
                        logger.debug('text input %s', input_data)
                    elif job_input['type'] == TYPE_LIST:
                        input_data = ''.join(random.sample(string.letters, 15))
                    else:
                        input_data = ''.join(random.sample(string.letters, 15))
                        logger.warn('default ???? %s %s', input_data, job_input['type'])
                    input_datas[job_input['name']] = input_data

                logger.debug('Data posted %s', input_datas)
                logger.debug('To => %s', submission['submission_uri'])
                o = urlparse(servicetool['url'])
                path = o.path.split('/')
                self.client.login(username="api_user", password="api_user")
                response = self.client.post(submission['submission_uri'],
                                            data=input_datas,
                                            format='multipart')
                logger.debug(response)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                job = Job.objects.all().order_by('-created').first()
                logger.debug(job)
        for job in Job.objects.all():
            logger.debug('Job %s ', job)
            self.assertEqual(job.status, waves.wcore.adaptors.const.JOB_CREATED)
            self.assertEqual(job.job_history.count(), 1)
            self.assertIsNotNone(job.job_inputs)
            self.assertIsNotNone(job.outputs)
            self.assertGreaterEqual(job.outputs.count(), 2)
        self.assertEqual(expected_jobs, Job.objects.count())

    def test_update_job(self):
        pass

    def test_delete_job(self):
        pass

    def test_job_error(self):
        pass

    def test_get_status(self):
        pass


class WavesAPIV2TestCase(BaseAPITestCase):
    def test_api_root(self):
        api_root = self.client.get(reverse('wapi:api_v2:api-root'))
        self.assertEqual(api_root.status_code, status.HTTP_200_OK)
        logger.debug('Results: %s ', api_root.data)
        self.assertIn('services', api_root.data.keys())
        self.assertIn('jobs', api_root.data.keys())
        tool_list = self.client.get(api_root.data['services'], format='json')
        self.assertIsNotNone(tool_list.data)
        logger.debug(tool_list.data)
        for service in tool_list.data:
            self.assertIn('url', service.keys())
            logger.debug('ServiceTool url: %s', service['url'])
            tool_details = self.client.get(service['url'], format='json')
            logger.debug('ServiceTool: %s', tool_details.data['name'])
            self.assertIsNotNone(tool_details.data['submissions'])

    def test_http_methods(self):
        # TODO test authorization
        pass

    def test_create_job_api(self):
        """
        Ensure for any service, we can create a job according to retrieved parameters
        """
        import random
        import string
        logger.debug('Retrieving service-list from ' + reverse('wapi:api_v2:waves-services-list'))
        logger.debug('1 %s service loaded ' % Service.objects.count())
        expected_jobs = 0
        for service in Service.objects.all():
            logger.debug("'%s' (%s) is available with %s submission(s)" % (
                service.name, service.get_status_display(), service.submissions_api.count()))
            expected_jobs += service.submissions_api.count()
        tool_list = self.client.get(reverse('wapi:api_v2:waves-services-list'), format="json")
        self.assertEqual(tool_list.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(tool_list)
        logger.debug(tool_list.data)
        for servicetool in tool_list.data:
            logger.debug('Creating job submission for %s %s', servicetool['name'], str(servicetool['version']))
            # for each servicetool retrieve inputs
            self.assertIsNotNone(servicetool['url'])
            detail = self.client.get(servicetool['url'])
            # logger.debug('Details data: %s', detail)
            tool_data = detail.data
            self.assertTrue('submissions' in tool_data)
            i = 0
            job_inputs_params = {}
            job_inputs_files = {}

            submissions = tool_data.get('submissions')
            logger.debug(submissions)
            for submission_url in submissions:
                submission_srv = self.client.get(submission_url)
                self.assertEqual(submission_srv.status_code, status.HTTP_200_OK)
                submission = submission_srv.data
                logger.debug(submission_srv.data)
                for name in submission['expected_inputs']:
                    logger.info('name %s ', name)
                    submission_input = submission['expected_inputs'][name]
                    if submission_input['type'] == TYPE_FILE:
                        i += 1
                        job_input_data = self.create_test_file(submission_input['api_name'], i)
                        job_input_file = self.create_test_file(submission_input['api_name'], i)
                        job_inputs_params[name] = job_input_data
                        job_inputs_files[name] = job_input_file
                        logger.debug('file input %s', job_input_data)
                    elif submission_input['type'] == TYPE_INT:
                        job_input_data = int(random.randint(0, 199))
                        job_inputs_params[name] = job_input_data
                        logger.debug('number input%s', job_input_data)
                    elif submission_input['type'] == TYPE_DECIMAL:
                        job_input_data = int(random.randint(0, 199))
                        job_inputs_params[name] = job_input_data
                        logger.debug('number input%s', job_input_data)
                    elif submission_input['type'] == TYPE_BOOLEAN:
                        job_input_data = random.randrange(100) < 50
                        job_inputs_params[name] = job_input_data
                    elif submission_input['type'] == TYPE_TEXT:
                        job_input_data = ''.join(random.sample(string.letters, 15))
                        job_inputs_params[name] = job_input_data
                        logger.debug('text input %s', job_input_data)
                    elif submission_input['type'] == TYPE_LIST:
                        job_input_data = ''.join(random.sample(string.letters, 15))
                        job_inputs_params[name] = job_input_data
                    else:
                        job_input_data = ''.join(random.sample(string.letters, 15))
                        logger.warn('default ???? %s %s', job_input_data, submission_input['type'])
                        job_inputs_params[name] = job_input_data
                logger.debug('Data posted %s', job_inputs_params)
                submit_to = submission['jobs']
                logger.debug('To => %s', submit_to)
                self.login('api_user')
                response = self.client.post(submit_to,
                                            data=job_inputs_params,
                                            files=job_inputs_files,
                                            format='multipart')
                logger.debug(response)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                job = Job.objects.get(slug=response.data['slug'])
                self.assertEqual(job.email_to, 'wavesapi@waves.wcore.fr')
                self.assertEqual
                logger.debug(job)
        for job in Job.objects.all():
            logger.debug('Job %s ', job)
            self.assertEqual(job.status, waves.wcore.adaptors.const.JOB_CREATED)
            self.assertEqual(job.job_history.count(), 1)
            self.assertIsNotNone(job.job_inputs)
            self.assertIsNotNone(job.outputs)
            self.assertGreaterEqual(job.outputs.count(), 2)
        self.assertEqual(expected_jobs, Job.objects.count())

    def test_cancel_job(self):
        """
        Test job cancel service
        """
        runner = Runner.objects.create(name="Mock Runner",
                                       clazz='waves.wcore.adaptors.mocks.MockJobRunnerAdaptor')

        sample_job = self.create_random_job(service=self.create_random_service(runner))
        response = self.client.get(reverse('wapi:api_v2:waves-jobs-detail', kwargs={'slug': sample_job.slug}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        test_cancel = self.client.put(reverse('wapi:api_v2:waves-jobs-cancel', kwargs={'slug': sample_job.slug}))
        self.assertEqual(test_cancel.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.login(username="api_user", password="api_user")
        test_cancel = self.client.put(reverse('wapi:api_v2:waves-jobs-cancel', kwargs={'slug': sample_job.slug}))
        self.assertEqual(test_cancel.status_code, status.HTTP_202_ACCEPTED)
        test_cancel = self.client.put(reverse('wapi:api_v2:waves-jobs-cancel', kwargs={'slug': sample_job.slug}))
        self.assertEqual(test_cancel.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_job(self):
        runner = Runner.objects.create(name="Mock Runner",
                                       clazz='waves.wcore.adaptors.mocks.MockJobRunnerAdaptor')

        sample_job = self.create_random_job(service=self.create_random_service(runner))
        response = self.client.get(reverse('wapi:api_v2:waves-jobs-detail', kwargs={'slug': sample_job.slug}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        test_delete = self.client.delete(reverse('wapi:api_v2:waves-jobs-detail', kwargs={'slug': sample_job.slug}))
        self.assertEqual(test_delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_missing_params(self):
        response = self.client.get(reverse('wapi:api_v2:waves-services-detail',
                                           kwargs={'api_name': 'physic_ist'}))
        if response.status_code == status.HTTP_200_OK:
            jobs_params = self.load_service_jobs_params(api_name='physic_ist')
            submitted_input = jobs_params[0]
            submitted_input.pop('s')
            logger.debug('Data posted %s', submitted_input)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.client.login(username="api_user", password="api_user")
            response = self.client.post(response.data['default_submission_uri'],
                                        data=submitted_input,
                                        format='multipart')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            logger.info(response)
        else:
            self.skipTest("Service physic_ist not available on wapi:api_v2 [status_code:%s]" % response.status_code)
