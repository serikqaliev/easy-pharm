from django.urls import path

from notifications.views import get_common_notifications, get_event_notifications, get_contact_notifications, \
    user_notifications

urlpatterns = [
    path('get_common_notifications/', get_common_notifications, name='get_common_notifications'),
    path('get_event_notifications/', get_event_notifications, name='get_event_notifications'),
    path('get_contact_notifications/', get_contact_notifications, name='get_contact_notifications'),
    path('user_notifications/', user_notifications, name='user_notifications'),
]
