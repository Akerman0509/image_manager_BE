
import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image_manager.settings')

app = Celery('image_manager')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()



# app.conf.beat_schedule = {
#     'sync-drive-folder-every-30-minutes': {
#         'task': 'applications.my_app.tasks.sync_drive_folder_task',
#         'schedule': crontab(minute='*/30'),  # every 30 mins
#         'args': (1, 'your_drive_folder_id_here', 'your_access_token_here'),
#     },
# }


# from django_celery_beat.models import CrontabSchedule, PeriodicTask
# import json

# schedule, _ = CrontabSchedule.objects.get_or_create(
#     minute='20',
#     hour='17',
#     day_of_week='*',
#     day_of_month='*',
#     month_of_year='*',
#     timezone='Asia/Ho_Chi_Minh'
# )

# PeriodicTask.objects.update_or_create(
#     name='Daily Drive Sync',
#     defaults={
#         'crontab': schedule,
#         'task': 'applications.my_app.tasks.sync_drive_folder_task',
#         'args': json.dumps([1, 'your_drive_folder_id', 'your_access_token']),
#     }
# )