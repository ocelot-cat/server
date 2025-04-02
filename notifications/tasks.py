from celery import shared_task
from .models import Notification


@shared_task
def create_notifications(user_ids, notification_type, message, related_object_id=None):
    notifications = [
        Notification(
            user_id=user_id,
            notification_type=notification_type,
            message=message,
            related_object_id=related_object_id,
        )
        for user_id in user_ids
    ]
    Notification.objects.bulk_create(notifications)
