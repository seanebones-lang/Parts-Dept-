from celery import Celery
from backend.config import settings

celery_app = Celery(
    'parts_dept_workers',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['backend.workers.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

celery_app.conf.beat_schedule = {
    'process-inbox-every-5-minutes': {
        'task': 'backend.workers.tasks.process_inbox_task',
        'schedule': 300.0,
    },
    'check-low-stock-daily': {
        'task': 'backend.workers.tasks.check_low_stock_task',
        'schedule': 86400.0,
    },
}

