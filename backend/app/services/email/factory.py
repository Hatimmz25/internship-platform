from app.services.email.base import BaseEmailProvider
from app.services.email.console import ConsoleEmailProvider
from app.services.email.smtp import SMTPEmailProvider
from app.services.email.resend_adapter import ResendEmailProvider
from app.core.config import settings

def get_email_provider() -> BaseEmailProvider:
    """Returns the configured email provider, falling back to Console for dev."""
    provider_name = getattr(settings, "EMAIL_PROVIDER", "console").lower()
    
    if provider_name == "resend" and getattr(settings, "RESEND_API_KEY", ""):
        return ResendEmailProvider()
    elif provider_name == "smtp" and getattr(settings, "SMTP_HOST", ""):
        return SMTPEmailProvider()
    
    return ConsoleEmailProvider()