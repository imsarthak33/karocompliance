"""
Celery Configuration — Production-grade task queue.

SEV-1 FIX (Celery Deadlocks / Document Swallowing):
  - acks_late=True: task is acknowledged ONLY after completion/explicit failure.
    Without this, if a Cloud Run instance is killed mid-task, the message is
    irrecoverably lost (the broker already deleted it on delivery).
  - reject_on_worker_lost=True: if the worker process dies, the task returns
    to the queue instead of being buried in an 'unacknowledged' limbo.
  - visibility_timeout must exceed your longest task. NIM calls can take 60s+;
    set to 1 hour to prevent double-execution from broker timeouts.
  - Max concurrency=2 to prevent RAM exhaustion on Cloud Run (NIM responses
    are large; parallel asyncio.run() calls will spike memory).
"""
import os
from celery import Celery  # type: ignore

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "karocompliance",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.document_tasks",
        "app.tasks.reconciliation_tasks",
        "app.tasks.reminder_tasks",
    ],
)

celery_app.conf.update(
    # --- Serialization ---
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,

    # --- SEV-1: Late Acknowledgement (prevent document swallowing) ---
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # --- Visibility Timeout: must be > longest task (NIM can be slow) ---
    broker_transport_options={
        "visibility_timeout": 3600,  # 1 hour
    },

    # --- Retry & Backoff Defaults ---
    task_max_retries=3,
    task_default_retry_delay=60,  # seconds

    # --- Concurrency: limit RAM usage on serverless workers ---
    worker_concurrency=2,
    worker_prefetch_multiplier=1,  # fetch one task at a time per worker slot

    # --- Result Expiry: don't fill Redis with stale results ---
    result_expires=86400,  # 24 hours
)
