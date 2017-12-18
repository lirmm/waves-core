import json
import logging
from unittest import skip
from django.urls import reverse

from waves.wcore.models import get_service_model, get_submission_model
from waves.wcore.tests.base import BaseTestCase
from waves.wcore.serializers import ServiceSerializer

logger = logging.getLogger(__name__)
Service = get_service_model()
Submission = get_submission_model()


class TestServices(BaseTestCase):
    def test_create_service(self):
        services = self.bootstrap_services()
        self.assertGreater(len(services), 0)
        for service in services:
            self.assertEqual(service.submissions.count(), 1)
            # Assert that service params has a length corresponding to 'allowed override' value
            self.assertListEqual(sorted(service.run_params.keys()), sorted(service.runner.run_params.keys()))

    @skip("Serialize / Unserialize needs code refactoring")
    def test_serialize_service(self):
        self.bootstrap_services()
        init_count = Service.objects.all().count()
        self.assertGreater(init_count, 0)
        file_paths = []
        for srv in Service.objects.all():
            file_paths.append(srv.serialize())
        for exp in file_paths:
            with open(exp) as fp:
                serializer = ServiceSerializer(data=json.load(fp))
                if serializer.is_valid():
                    serializer.save()
        self.assertEqual(init_count * 2, Service.objects.all().count())

    def test_access_rules(self):
        def _test_access(url, expected_status, user=None):
            self.login(user) if user else None
            response = self.client.get(url)
            self.assertEqual(response.status_code, expected_status,
                             "Status code {} expected is {}".format(response.status_code, expected_status))
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
        url = reverse('wcore:service_details', kwargs={'slug': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 403, 'api_user')
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'slug': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 403, 'api_user')
        logger.debug('Test DRAFT status OK')
        logger.debug('Test TEST status ...')
        service.status = service.SRV_TEST
        service.created_by = self.users['superadmin']
        service.save()
        url = reverse('wcore:service_details', kwargs={'slug': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 403, 'api_user')
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'slug': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 403, 'api_user')
        logger.debug('Test TEST status OK')

        logger.debug('Test REGISTERED status ...')
        service.status = service.SRV_REGISTERED
        service.save()
        url = reverse('wcore:service_details', kwargs={'slug': service.api_name})
        _test_access(url, 200)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 200, 'api_user')
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'slug': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 200, 'api_user')
        logger.debug('Test REGISTERED status OK')

        logger.debug('Test RESTRICTED status ...')
        service.status = service.SRV_RESTRICTED
        service.save()
        url = reverse('wcore:service_details', kwargs={'slug': service.api_name})
        _test_access(url, 200)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 200, 'api_user')
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'slug': service.api_name})
        _test_access(url, 403)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 403, 'api_user')
        # Add api_user to restricted client
        service.restricted_client.add(self.users['api_user'])
        service.save()
        _test_access(url, 200, 'api_user')
        logger.debug('Test RESTRICTED status OK')
        logger.debug('Test PUBLIC status ...')
        service.status = service.SRV_PUBLIC
        service.save()
        url = reverse('wcore:service_details', kwargs={'slug': service.api_name})
        _test_access(url, 200)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 200, 'api_user')
        # SAME for submission
        url = reverse('wcore:job_submission', kwargs={'slug': service.api_name})
        _test_access(url, 200)
        _test_access(url, 200, 'superadmin')
        _test_access(url, 200, 'admin')
        _test_access(url, 200, 'api_user')
        logger.debug('Test PUBLIC status OK')
