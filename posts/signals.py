from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import Notification
from posts.models import Comment, Like, Repost


@receiver(post_save, sender=Like)
def notify_post_like(sender, instance, created, **kwargs):
    if not created or not instance.post or instance.post.author == instance.user:
        return
    Notification.objects.create(
        recipient=instance.post.author,
        sender=instance.user,
        notification_type="like",
        post=instance.post,
        message=f"{instance.user.full_name} liked your post.",
    )


@receiver(post_save, sender=Comment)
def notify_post_comment(sender, instance, created, **kwargs):
    if not created or instance.post.author == instance.author:
        return
    Notification.objects.create(
        recipient=instance.post.author,
        sender=instance.author,
        notification_type="comment",
        post=instance.post,
        comment=instance,
        message=f"{instance.author.full_name} commented on your post.",
    )


@receiver(post_save, sender=Repost)
def notify_post_repost(sender, instance, created, **kwargs):
    if not created or instance.post.author == instance.user:
        return
    Notification.objects.create(
        recipient=instance.post.author,
        sender=instance.user,
        notification_type="repost",
        post=instance.post,
        message=f"{instance.user.full_name} reposted your post.",
    )
