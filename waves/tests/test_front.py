"""
Unit test some front pages rendenring
"""
from __future__ import unicode_literals

from django.test import TestCase
from django.core.urlresolvers import reverse


class WavesPagesTestCase(TestCase):
    """ Test pages rendering """
    def test_home_page_exists(self):
        url = reverse('home')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_about_page_exists(self):
        url = reverse('waves:about')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
