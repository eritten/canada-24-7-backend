from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from canada247.api import paginated_response, success_response
from notifications.models import DeviceToken, Notification
from notifications.serializers import DeviceTokenSerializer, NotificationSerializer


class StandardPagination(PageNumberPagination):
    page_size = 20


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return Notification.objects.select_related("sender", "sender__profile").filter(recipient=self.request.user)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True)
        return paginated_response(self.paginator.get_paginated_response(serializer.data).data)


class MarkAllNotificationsReadView(APIView):
    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return success_response(message="All notifications marked as read.")


class MarkNotificationReadView(APIView):
    def post(self, request, pk):
        notification = generics.get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return success_response(message="Notification marked as read.")


class NotificationUnreadCountView(APIView):
    def get(self, request):
        return success_response(data={"count": Notification.objects.filter(recipient=request.user, is_read=False).count()})


class DeviceRegisterView(APIView):
    def post(self, request):
        serializer = DeviceTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        DeviceToken.objects.update_or_create(
            token=serializer.validated_data["token"],
            defaults={"user": request.user, "platform": serializer.validated_data["platform"]},
        )
        return success_response(message="Device registered successfully.", status_code=status.HTTP_201_CREATED)
