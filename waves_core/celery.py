from __future__ import absolute_import, unicode_literals
from celery import Celery
import os

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "waves_core.settings")
django.setup()

app = Celery('waves_core', broker_pool_limit=1, broker='redis://localhost:6379', result_backend='redis://localhost:6379')
app.autodiscover_tasks()