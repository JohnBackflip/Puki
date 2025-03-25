# notification/providers/sms.py
from twilio.rest import Client
import os

class SMSProvider:
    def __init__(self):
        self.client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.from_number = os.getenv("TWILIO_FROM_NUMBER")
    
    async def send_sms(self, to_number: str, message: str) -> bool:
        try:
            self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            return True
        except Exception as e:
            print(f"SMS sending failed: {str(e)}")
            return False