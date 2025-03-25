# notification/providers/push.py
from firebase_admin import messaging, credentials, initialize_app
import os

class PushNotificationProvider:
    def __init__(self):
        cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
        initialize_app(cred)
    
    async def send_push(self, token: str, title: str, body: str, data: dict = None) -> bool:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token
            )
            
            messaging.send(message)
            return True
        except Exception as e:
            print(f"Push notification failed: {str(e)}")
            return False