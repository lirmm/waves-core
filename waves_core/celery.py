from celery import Celery
from django.conf import settings
import os

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "waves_core.settings")
django.setup()

app = Celery('waves.core', broker_pool_limit=1, broker=settings.URL_BROKER, result_backend=settings.URL_BROKER)
app.autodiscover_tasks()
