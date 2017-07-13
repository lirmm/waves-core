from __future__ import unicode_literals

import logging
from urlparse import urlparse

import waves.wcore.adaptors.const
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from waves.wcore.models import Job
from waves.wcore.models.inputs import AParam
from waves.wcore.tests.base import WavesBaseTestCase
from waves.wcore.tests.utils import create_test_file

logger = logging.getLogger(__name__)
User = get_user_model()


class WavesAPITestCase(APITestCase, WavesBaseTestCase):
    fixtures = ['waves/core/tests/fixtures/services.json']

    def setUp(self):
        super(WavesAPITestCase, self).setUp()
        super_user = User.objects.create(email='superadmin@waves.wcore.fr', username="superadmin", is_superuser=True)
        super_user.set_password('superadmin1234')
        super_user.save()
        admin_user = User.objects.create(email='admin@waves.wcore.fr', username="admin", is_staff=True)
        admin_user.set_password('admin1234')
        admin_user.save()

        api_user = User.objects.create(email="waves:api@waves.wcore.fr", username="api_user", is_staff=False,
                                       is_superuser=False, is_active=True)
        api_user.set_password('api_user1234')
        api_user.save()
        self.users = {'api_user': api_user, 'admin': admin_user, 'root': super_user}

    def test_api_root(self):
        for api_version in ('api_v1', 'api_v2'):
            api_root = self.client.get(reverse('waves:' + api_version + ':api-root'))
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
                self.assertIsNotNone(tool_details.data['default_submission_uri'])

    def testHTTPMethods(self):
        # TODO test authorization
        pass

    def test_create_job(self):
        """
        Ensure for any service, we can create a job according to retrieved parameters
        """
        import random
        import string
        logger.debug('Retrieving service-list from ' + reverse('waves:api_v2:waves-services-list'))
        for api_version in ('api_v1', 'api_v2'):
            tool_list = self.client.get(reverse('waves:'+api_version+':waves-services-list'), format="json")
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
                for submission in submissions:
                    for job_input in submission['inputs']:
                        if job_input['type'] == AParam.TYPE_FILE:
                            i += 1
                            input_data = create_test_file(job_input['name'], i)
                            # input_datas[job_input['name']] = input_data.name
                            logger.debug('file input %s', input_data)
                        elif job_input['type'] == AParam.TYPE_INT:
                            input_data = int(random.randint(0, 199))
                            logger.debug('number input%s', input_data)
                        elif job_input['type'] == AParam.TYPE_DECIMAL:
                            input_data = int(random.randint(0, 199))
                            logger.debug('number input%s', input_data)
                        elif job_input['type'] == AParam.TYPE_BOOLEAN:
                            input_data = random.randrange(100) < 50
                        elif job_input['type'] == AParam.TYPE_TEXT:
                            input_data = ''.join(random.sample(string.letters, 15))
                            logger.debug('text input %s', input_data)
                        elif job_input['type'] == AParam.TYPE_LIST:
                            input_data = ''.join(random.sample(string.letters, 15))
                        else:
                            input_data = ''.join(random.sample(string.letters, 15))
                            logger.warn('default ???? %s %s', input_data, job_input['type'])
                        input_datas[job_input['name']] = input_data

                    logger.debug('Data posted %s', input_datas)
                    logger.debug('To => %s', submission['submission_uri'])
                    o = urlparse(servicetool['url'])
                    path = o.path.split('/')
                    self.client.login(username="api_user",  password="api_user1234")
                    response = self.client.post(submission['submission_uri'],
                                                data=input_datas,
                                                format='multipart')
                    logger.debug(response)
                    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                    job = Job.objects.all().order_by('-created').first()
                    logger.debug(job)
        jobs = Job.objects.all()
        for job in jobs:
            logger.debug('Job %s ', job)
            self.assertEqual(job.status, waves.wcore.adaptors.const.JOB_CREATED)
            self.assertEqual(job.job_history.count(), 1)
            self.assertIsNotNone(job.job_inputs)
            self.assertIsNotNone(job.outputs)
            self.assertGreaterEqual(job.outputs.count(), 2)
        self.assertEqual(2, Job.objects.count())

    def test_update_job(self):
        pass

    def test_delete_job(self):
        pass

    def test_job_error(self):
        pass

    def test_get_status(self):
        pass

    def testPhysicIST(self):
        url_post = self.client.get(reverse('waves:api_v2:waves-services-detail',
                                           kwargs={'api_name': 'physic_ist'}))
        if url_post.status_code == status.HTTP_200_OK:

            jobs_params = self._loadServiceJobsParams(api_name='physic_ist')

            for submitted_input in jobs_params:
                logger.debug('Data posted %s', submitted_input)
                response = self.client.post(url_post.data['default_submission_uri'],
                                            data=submitted_input,
                                            format='multipart')
                logger.debug(response)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                job_details = self.client.get(reverse('waves:api_v2:waves-jobs-detail',
                                                      kwargs={'slug': response.data['slug']}))

                self.assertEqual(job_details.status_code, status.HTTP_200_OK)
                job = Job.objects.get(slug=response.data['slug'])
                self.assertIsInstance(job, Job)
                self.assertEqual(job.status, Job.JOB_CREATED)
        else:
            self.skipTest("Service physic_ist not available on waves:api_v2 [status_code:%s]" % url_post.status_code)

    def testMissingParam(self):
        response = self.client.get(reverse('waves:api_v2:waves-services-detail',
                                           kwargs={'api_name': 'physic_ist'}))
        if response.status_code == status.HTTP_200_OK:
            jobs_params = self._loadServiceJobsParams(api_name='physic_ist')
            submitted_input = jobs_params[0]
            submitted_input.pop('s')
            logger.debug('Data posted %s', submitted_input)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.client.login(username="api_user", password="api_user1234")
            response = self.client.post(response.data['default_submission_uri'],
                                        data=submitted_input,
                                        format='multipart')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            logger.info(response)
        else:
            self.skipTest("Service physic_ist not available on waves:api_v2 [status_code:%s]" % response.status_code)
