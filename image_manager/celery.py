
import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image_manager.settings')

app = Celery('image_manager')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# app.conf.beat_schedule = {
#     'sync-drive-folder-every-15-minutes': {
#         'task': 'applications.my_app.tasks.sync_drive_folder_task',
#         'schedule': crontab(minute='*/2'),  # every 15 minutes
#         'args': (None, None, ''),  # Default: do nothing / no user or folder
#     },
# }
