

import logging

from django.urls import reverse

from waves.core.models import Service, Submission
from waves.core.tests.base import BaseTestCase

logger = logging.getLogger(__name__)




class ServicesTestCase(BaseTestCase):
    def test_create_service(self):
        services = self.bootstrap_services()
        self.assertGreater(len(services), 0)
        for service in services:
            self.assertEqual(service.submissions.count(), 1)
            # Assert that service params has a length corresponding to 'allowed override' value
            self.assertListEqual(sorted(service.run_params.keys()), sorted(service.runner.run_params.keys()))

    def test_access_rules(self):
        def _test_access(the_url, expected_status, user=None):
            self.login(user) if user else None
            the_response = self.client.get(url)
            self.assertEqual(the_response.status_code, expected_status,
                             "{} Status code {} [expected: {}]".format(the_url, the_response.status_code, expected_status))
            self.client.logout() if user else None

        services = self.bootstrap_services()
        self.assertGreater(len(services), 0)
        # List access => always 200
        response = self.client.get(reverse('wcore:services_list'))
        self.assertEqual(response.status_code, 200)
        service = services[0]
        # For draft Service is allowed only to creator and superadmin
        logger.debug('Test DRAFT status ...')
        service.status = service.SRV_DRAFT
        service.created_by = self.users['admin']
        service.save()
        url = reverse('wcore:service_details', kwargs={'service_app_name': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 403, 'api_user')
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'service_app_name': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 403, 'api_user')
        logger.debug('Test DRAFT status OK')
        logger.debug('Test TEST status ...')
        service.status = service.SRV_TEST
        service.created_by = self.users['superadmin']
        service.save()
        url = reverse('wcore:service_details', kwargs={'service_app_name': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 403, 'api_user')
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'service_app_name': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 403, 'api_user')
        logger.debug('Test TEST status OK')

        logger.debug('Test REGISTERED status ...')
        service.status = service.SRV_REGISTERED
        service.save()
        url = reverse('wcore:service_details', kwargs={'service_app_name': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 200, 'api_user')
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'service_app_name': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 200, 'api_user')
        logger.debug('Test REGISTERED status OK')

        logger.debug('Test RESTRICTED status ...')
        service.status = service.SRV_RESTRICTED
        service.save()
        url = reverse('wcore:service_details', kwargs={'service_app_name': service.api_name})
        url_service = reverse('wcore:service_details', kwargs={'service_app_name': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 403, 'api_user')
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'service_app_name': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 403, 'api_user')
        # Add api_user to restricted client
        service.restricted_client.add(self.users['api_user'])
        service.save()
        _test_access(url_service, 200, 'api_user')
        _test_access(url, 200, 'api_user')
        logger.debug('Test RESTRICTED status OK')
        logger.debug('Test PUBLIC status ...')
        service.status = service.SRV_PUBLIC
        service.save()
        url = reverse('wcore:service_details', kwargs={'service_app_name': service.api_name})
        _test_access(url, 200)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 200, 'api_user')
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'service_app_name': service.api_name})
        _test_access(url, 200)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 200, 'api_user')
        logger.debug('Test PUBLIC status OK')
