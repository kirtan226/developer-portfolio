import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "developer_portfolio.settings")

app = Celery("developer_portfolio")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()