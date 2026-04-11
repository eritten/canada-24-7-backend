from django.urls import path

from notifications import views


urlpatterns = [
    path("notifications/", views.NotificationListView.as_view(), name="notifications-list"),
    path("notifications/read-all/", views.MarkAllNotificationsReadView.as_view(), name="notifications-read-all"),
    path("notifications/<uuid:pk>/read/", views.MarkNotificationReadView.as_view(), name="notifications-read"),
    path("notifications/unread-count/", views.NotificationUnreadCountView.as_view(), name="notifications-unread-count"),
    path("devices/register/", views.DeviceRegisterView.as_view(), name="devices-register"),
]
