from rest_framework import status
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notifications.models import Notification
from notifications.serializers import CommonNotificationsSerializer, EventNotificationsSerializer, \
    ContactNotificationsSerializer, ShortEventNotificationSerializer, \
    ShortContactNotificationSerializer, ShortCommonNotificationSerializer


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_common_notifications(request):
    notifications = Notification.objects.filter(user=request.user, notification_type="Common")
    serializer = CommonNotificationsSerializer(notifications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_event_notifications(request):
    Notification.objects.filter(user=request.user, notification_type="Event").update(is_read=True)
    notifications = Notification.objects.filter(user=request.user, notification_type="Event")
    serializer = EventNotificationsSerializer(notifications, context={'user': request.user}, many=True)

    Notification.objects.filter(user=request.user, notification_type="Event").update(is_read=True)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_contact_notifications(request):
    notifications = Notification.objects.filter(user=request.user, notification_type="Contact")
    serializer = ContactNotificationsSerializer(notifications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def user_notifications(request):
    last_event_notification = Notification.objects.filter(user=request.user, notification_type="Event").first()
    last_contact_notification = Notification.objects.filter(user=request.user, notification_type="Contact").first()
    last_common_notification = Notification.objects.filter(user=request.user, notification_type="Common").first()

    last_event_notification_data = None
    last_contact_notification_data = None
    last_common_notification_data = None

    if last_event_notification:
        last_event_notification_data = ShortEventNotificationSerializer(last_event_notification).data
    if last_contact_notification:
        last_contact_notification_data = ShortContactNotificationSerializer(last_contact_notification).data
    if last_common_notification:
        last_common_notification_data = ShortCommonNotificationSerializer(last_common_notification).data

    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    data = {
        'event': last_event_notification_data,
        'contact': last_contact_notification_data,
        'common': last_common_notification_data,
        'unread_count': unread_count,
    }

    return Response(data, status=status.HTTP_200_OK)



