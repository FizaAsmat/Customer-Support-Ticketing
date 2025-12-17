import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Customer_Ticketing.settings")

app = Celery("Customer_Ticketing")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
