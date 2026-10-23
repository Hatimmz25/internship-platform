import logging
from app.services.email.base import BaseEmailProvider

logger = logging.getLogger(__name__)

class ConsoleEmailProvider(BaseEmailProvider):
    """Development fallback provider that prints emails to the console."""
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        logger.info(f"========== EMAIL DISPATCHED TO: {to_email} ==========")
        logger.info(f"SUBJECT: {subject}")
        logger.info(f"TEXT BODY:\n{text_content}")
        logger.info("=======================================================")
        return True