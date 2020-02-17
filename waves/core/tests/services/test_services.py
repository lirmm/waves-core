import logging

from django.test import TestCase
from django.urls import reverse

from waves.core.tests.utils import bootstrap_services, api_user, super_user, admin_user

logger = logging.getLogger(__name__)


class WavesServicesTestCase(TestCase):
    fixtures = ("waves/core/tests/fixtures/accounts.json",)

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
