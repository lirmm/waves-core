from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ApiKeyConfig(AppConfig):
    name = 'waves.authentication'
    verbose_name = _("WAVES Api Authentication")

    def ready(self):
        """
        Executed once when WAVES application startup !
        Just import waves signals
        :return: None
        """
        import waves.authentication.signals
