from django.conf import settings

import requests

from notifications.models import DeviceToken


def send_push_notification(notification):
    if not settings.EXPO_PUSH_ENABLED:
        return

    tokens = list(DeviceToken.objects.filter(user=notification.recipient).values_list("token", flat=True))
    if not tokens:
        return

    payload = [
        {
            "to": token,
            "title": "Canada 24/7",
            "body": notification.message,
            "data": {
                "notificationId": str(notification.id),
                "type": notification.notification_type,
                "postId": str(notification.post_id) if notification.post_id else None,
            },
            "sound": "default",
        }
        for token in tokens
    ]

    try:
        requests.post(
            settings.EXPO_PUSH_API_URL,
            json=payload,
            headers={"Accept": "application/json", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/json"},
            timeout=10,
        )
    except requests.RequestException:
        return
