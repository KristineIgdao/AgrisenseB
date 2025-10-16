# agrisense/asgi.py
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from agrisense import routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agrisense.settings")

# Initialize Django *before* importing anything else
django.setup()

# Now safe to import middleware
from accounts.middleware import JWTAuthMiddleware

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(routing.websocket_urlpatterns)
    ),
})
