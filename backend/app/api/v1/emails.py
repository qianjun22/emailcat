from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any
from app.core.auth import get_current_user
from app.services.email_service import EmailService, GmailService, OutlookService
from app.core.config import settings
from pydantic import BaseModel

router = APIRouter()

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str

def get_email_service(provider: str) -> EmailService:
    if provider == "gmail":
        return GmailService(settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET)
    elif provider == "outlook":
        return OutlookService(settings.MICROSOFT_CLIENT_ID, settings.MICROSOFT_CLIENT_SECRET)
    else:
        raise HTTPException(status_code=400, detail="Unsupported email provider")

@router.get("/unread")
async def get_unread_emails(
    provider: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get unread emails for the current user"""
    service = get_email_service(provider)
    return await service.get_unread_emails(current_user["sub"])

@router.post("/send")
async def send_email(
    provider: str,
    email_data: EmailRequest = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Send an email on behalf of the current user"""
    service = get_email_service(provider)
    success = await service.send_email(
        current_user["sub"],
        email_data.to,
        email_data.subject,
        email_data.body
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")
    return {"message": "Email sent successfully"}

@router.post("/mark-read/{email_id}")
async def mark_email_as_read(
    email_id: str,
    provider: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Mark an email as read"""
    service = get_email_service(provider)
    success = await service.mark_as_read(current_user["sub"], email_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to mark email as read")
    return {"message": "Email marked as read successfully"} 