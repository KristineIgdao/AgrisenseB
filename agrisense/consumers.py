# agrisense/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json, random, asyncio

class SoilConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user or user.is_anonymous:
            print("❌ Anonymous user tried to connect to Soil WebSocket")
            await self.close()
            return

        self.user = user
        self.group_name = f"user_{user.id}_soil"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        print(f"✅ Soil WebSocket connected for user {user.username}")

        # 🪴 Start sending simulated soil data
        asyncio.create_task(self.send_fake_soil_data())

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"❌ Soil WebSocket disconnected for user {getattr(self, 'user', None)}")

    async def send_fake_soil_data(self):
        """
        Simulates sending soil data every 5 seconds for testing.
        In production, replace this with real sensor data or DB feed.
        """
        try:
            while True:
                fake_data = {
                    "temperature": round(random.uniform(20, 35), 1),
                    "ph": round(random.uniform(5.5, 7.5), 2),
                    "nitrogen": round(random.uniform(15, 50), 1),
                    "phosphorus": round(random.uniform(10, 40), 1),
                    "potassium": round(random.uniform(80, 250), 1),
                }

                await self.send(text_data=json.dumps({
                    "type": "soil_update",
                    "data": fake_data
                }))

                await asyncio.sleep(5)
        except Exception as e:
            print(f"⚠️ Soil data loop stopped: {e}")



class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if user.is_anonymous:
            print("❌ Anonymous user tried to connect to Notification WebSocket")
            await self.close()
            return

        self.group_name = f"user_{user.id}"

        # ✅ Add user to their notification group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"✅ Notification WebSocket connected for {user.username}")

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if not user.is_anonymous:
            await self.channel_layer.group_discard(f"user_{user.id}", self.channel_name)
        print(f"❌ Notification WebSocket disconnected for {user}")

    async def daily_summary(self, event):
        """Receive and send daily summary notifications"""
        await self.send(text_data=json.dumps({
            "type": "daily_summary",
            "title": event["title"],
            "message": event["message"],
            "summary": event["summary"],
            "date": event["date"],
        }))
