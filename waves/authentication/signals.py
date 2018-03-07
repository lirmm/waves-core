from __future__ import unicode_literals

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_api_key(sender, instance=None, created=False, **kwargs):
    if 'waves.authentication' in settings.INSTALLED_APPS:
        from waves.authentication.models import ApiKey
        if created or ApiKey.objects.filter(user=instance).count() == 0:
            ApiKey.objects.create(user=instance)
