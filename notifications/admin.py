from django.contrib import admin

from notifications.models import DeviceToken, Notification


admin.site.register(Notification)
admin.site.register(DeviceToken)
