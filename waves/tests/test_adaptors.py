from __future__ import unicode_literals

import logging

from django.test import TestCase

from waves.adaptors.loader import AdaptorLoader
from waves.settings import waves_settings

logger = logging.getLogger(__name__)


class TestAdaptors(TestCase):
    loader = AdaptorLoader()

    def test_loader(self):
        list_adaptors = self.loader.get_adaptors()
        self.assertTrue(all([clazz.__class__ in waves_settings.ADAPTORS_CLASSES for clazz in list_adaptors]))
        [logger.debug(c) for c in list_adaptors]
        # TODO add more tests ?

    def test_init(self):
        for adaptor in waves_settings.ADAPTORS_CLASSES:
            new_instance = self.loader.load(adaptor, host="localTestHost", protocol="httpTest", command="CommandTest")
            self.assertEqual(new_instance.host, "localTestHost")
            self.assertEqual(new_instance.command, "CommandTest")
            self.assertEqual(new_instance.protocol, "httpTest")





