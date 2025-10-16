# accounts/middleware.py
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async
import jwt


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        token_list = query_params.get("token")

        if token_list:
            token = token_list[0]
            try:
                access_token = AccessToken(token)
                user_id = access_token["user_id"]
                user = await self.get_user(user_id)
                scope["user"] = user
                print(f"✅ JWTAuthMiddleware authenticated user: {getattr(user, 'username', 'Anonymous')}")
            except jwt.ExpiredSignatureError:
                print("❌ JWT expired")
                scope["user"] = AnonymousUser()
            except Exception as e:
                print(f"❌ JWT decode error: {e}")
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @staticmethod
    @database_sync_to_async
    def get_user(user_id):
        from accounts.models import CustomUser  # imported inside, safe now
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return AnonymousUser()
