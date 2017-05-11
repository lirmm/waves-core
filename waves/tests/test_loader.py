from __future__ import unicode_literals

import inspect
import logging

from django.test import TestCase
from waves.adaptors.core.base import JobAdaptor, AdaptorImporter

from waves.addons.loader import load_core, load_extra_adaptors #, load_extra_importers

logger = logging.getLogger(__name__)


class TestLoadAddons(TestCase):

    def test_load_actions(self):
        core = load_core()
        self.assertTrue(all([not inspect.isabstract(clazz) for name, clazz in core]))
        [logger.debug(c) for c in core]
        addons = load_extra_adaptors()
        if len(addons) > 0:
            self.assertTrue(all([issubclass(addon[1], JobAdaptor) for addon in addons]))
        [logger.debug(c) for c in addons]
        """
        imps = load_extra_importers()
        if len(imps) > 0:
            self.assertTrue(all([issubclass(importer[1], AdaptorImporter) for importer in imps]))
        [logger.debug(c) for c in imps]
        """
