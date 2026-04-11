from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Follow
from notifications.models import Notification


@receiver(post_save, sender=Follow)
def notify_follow(sender, instance, created, **kwargs):
    if not created:
        return
    Notification.objects.create(
        recipient=instance.following,
        sender=instance.follower,
        notification_type="follow",
        message=f"{instance.follower.full_name} started following you.",
    )
