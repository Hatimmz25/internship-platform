import resend
import logging
from app.services.email.base import BaseEmailProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class ResendEmailProvider(BaseEmailProvider):
    """Resend API adapter for email delivery."""
    
    def __init__(self):
        resend.api_key = getattr(settings, "RESEND_API_KEY", "")
        self.sender = getattr(settings, "EMAIL_FROM", "alerts@internshipradar.ai")

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        if "\n" in to_email or "\r" in to_email:
            raise ValueError("Invalid email address format.")
            
        try:
            response = resend.Emails.send({
                "from": self.sender,
                "to": to_email,
                "subject": subject,
                "html": html_content,
                "text": text_content
            })
            logger.info(f"Resend delivered email to {to_email}, ID: {response.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Resend Delivery failed for {to_email}: {e}")
            raise