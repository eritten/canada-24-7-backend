from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import Notification
from notifications.services import send_push_notification


@receiver(post_save, sender=Notification)
def handle_notification_created(sender, instance, created, **kwargs):
    if not created:
        return
    send_push_notification(instance)
