from rest_framework import serializers

from notifications.models import DeviceToken, Notification


class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.full_name", read_only=True)
    sender_username = serializers.CharField(source="sender.profile.username", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "sender_name",
            "sender_username",
            "notification_type",
            "post",
            "comment",
            "message",
            "is_read",
            "created_at",
        )


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ("token", "platform")
