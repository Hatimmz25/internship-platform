from abc import ABC, abstractmethod
from typing import List, Optional

class BaseEmailProvider(ABC):
    """Abstract interface for all email delivery providers."""
    
    @abstractmethod
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: str
    ) -> bool:
        """
        Dispatches an email and returns True if accepted by the provider.
        Raises an exception if the provider returns a transient error.
        """
        pass