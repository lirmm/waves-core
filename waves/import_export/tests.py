import json
import logging

from import_export.services import ServiceSerializer
from waves.core.models import Service
from waves.core.tests.base import WavesTestCaseMixin

logger = logging.getLogger(__name__)


class SerializationTestCase(WavesTestCaseMixin):

    # @skip("Serialize / Unserialize needs code refactoring")
    def test_serialize_service(self):
        self.bootstrap_services()
        init_count = Service.objects.all().count()
        self.assertGreater(init_count, 0)
        file_paths = []
        for srv in Service.objects.all():
            file_out = srv.serialize()
            file_paths.append(file_out)
        for exp in file_paths:
            with open(exp) as fp:
                serializer = ServiceSerializer(data=json.load(fp))
                if serializer.is_valid():
                    serializer.save()
        self.assertEqual(init_count * 2, Service.objects.all().count())
