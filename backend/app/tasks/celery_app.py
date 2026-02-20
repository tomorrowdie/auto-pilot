"""
Celery application configuration for background tasks
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app instance
celery_app = Celery(
    'shopify_seo_analyzer',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Load configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'sync-stores-daily': {
        'task': 'app.tasks.sync_tasks.sync_all_stores',
        'schedule': crontab(hour=0, minute=0),  # Run at midnight UTC daily
    },
    'check-api-health-hourly': {
        'task': 'app.tasks.sync_tasks.check_stores_api_health',
        'schedule': crontab(minute=0),  # Run every hour
    },
}
