from __future__ import unicode_literals

import inspect
import logging

from django.test import TestCase

from waves.adaptors.loader import AdaptorLoader

logger = logging.getLogger(__name__)


class TestLoadAddons(TestCase):

    def test_load_actions(self):

        loader = AdaptorLoader()
        list_adaptors = loader.get_adaptors()
        self.assertTrue(all([not inspect.isabstract(clazz) for clazz in list_adaptors]))
        [logger.debug(c) for c in list_adaptors]

# TODO add more tests