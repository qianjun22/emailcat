from abc import ABC, abstractmethod
from typing import List, Dict, Any

class EmailService(ABC):
    @abstractmethod
    async def get_unread_emails(self, user_id: str) -> List[Dict[str, Any]]:
        """Get unread emails for a user"""
        pass
    
    @abstractmethod
    async def send_email(self, user_id: str, to: str, subject: str, body: str) -> bool:
        """Send an email on behalf of the user"""
        pass
    
    @abstractmethod
    async def mark_as_read(self, user_id: str, email_id: str) -> bool:
        """Mark an email as read"""
        pass

class GmailService(EmailService):
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    async def get_unread_emails(self, user_id: str) -> List[Dict[str, Any]]:
        # TODO: Implement Gmail API integration
        return [{"id": "1", "subject": "Test Email", "from": "test@example.com"}]
    
    async def send_email(self, user_id: str, to: str, subject: str, body: str) -> bool:
        # TODO: Implement Gmail API integration
        return True
    
    async def mark_as_read(self, user_id: str, email_id: str) -> bool:
        # TODO: Implement Gmail API integration
        return True

class OutlookService(EmailService):
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    async def get_unread_emails(self, user_id: str) -> List[Dict[str, Any]]:
        # TODO: Implement Microsoft Graph API integration
        return [{"id": "1", "subject": "Test Email", "from": "test@example.com"}]
    
    async def send_email(self, user_id: str, to: str, subject: str, body: str) -> bool:
        # TODO: Implement Microsoft Graph API integration
        return True
    
    async def mark_as_read(self, user_id: str, email_id: str) -> bool:
        # TODO: Implement Microsoft Graph API integration
        return True 