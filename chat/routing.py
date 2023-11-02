from django.urls import re_path
from .websocket_consumer import UserWebsocketConsumer

websocket_urlpatterns = [
    re_path(r'^ws/(?P<room_name>[^/]+)/$', UserWebsocketConsumer.as_asgi()),
]