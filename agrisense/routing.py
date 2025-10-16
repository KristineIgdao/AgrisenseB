from django.urls import re_path
from agrisense import consumers

websocket_urlpatterns = [
    re_path(r"ws/soil/$", consumers.SoilConsumer.as_asgi()),
    re_path(r"ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
]
