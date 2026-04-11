import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "canada247.settings")

app = Celery("canada247")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
