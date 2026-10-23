import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.services.email.base import BaseEmailProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class SMTPEmailProvider(BaseEmailProvider):
    """Standard SMTP adapter for email delivery."""
    
    def __init__(self):
        self.host = getattr(settings, "SMTP_HOST", "")
        self.port = getattr(settings, "SMTP_PORT", 587)
        self.user = getattr(settings, "SMTP_USER", "")
        self.password = getattr(settings, "SMTP_PASSWORD", "")
        self.sender = getattr(settings, "EMAIL_FROM", "alerts@internshipradar.ai")

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = to_email

        # Prevent Header Injection
        if "\n" in to_email or "\r" in to_email:
            raise ValueError("Invalid email address format.")

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.sender, to_email, msg.as_string())
            return True
        except Exception as e:
            logger.error(f"SMTP Delivery failed for {to_email}: {e}")
            raise