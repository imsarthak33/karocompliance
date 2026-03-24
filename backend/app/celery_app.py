import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "karocompliance",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks.document_tasks', 'app.tasks.reconciliation_tasks', 'app.tasks.reminder_tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
)
