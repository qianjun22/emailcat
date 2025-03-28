from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
from app.core.auth import get_current_user
from app.core.config import settings
import httpx
import logging

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get information about the currently authenticated user"""
    return {
        "id": current_user["sub"],
        "email": current_user.get("email"),
        "name": current_user.get("name")
    }

@router.get("/login")
async def login(request: Request, redirect_after_login: Optional[str] = None):
    """Redirect to Auth0 login page"""
    auth0_domain = settings.AUTH0_DOMAIN
    client_id = settings.AUTH0_CLIENT_ID
    redirect_uri = f"http://localhost:8000/api/v1/auth/callback"
    
    # Store the redirect URL in a cookie if provided
    if redirect_after_login:
        response = RedirectResponse(url=f"https://{auth0_domain}/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=openid profile email")
        response.set_cookie(
            key="redirect_after_login",
            value=redirect_after_login,
            httponly=True,
            max_age=600  # 10 minutes
        )
        return response
    
    # Regular Auth0 login
    auth_url = f"https://{auth0_domain}/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=openid profile email"
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def auth_callback(request: Request, code: str):
    """Handle Auth0 callback"""
    try:
        # Exchange code for token
        token_url = f"https://{settings.AUTH0_DOMAIN}/oauth/token"
        client_id = settings.AUTH0_CLIENT_ID
        client_secret = settings.AUTH0_CLIENT_SECRET
        redirect_uri = f"http://localhost:8000/api/v1/auth/callback"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            token_data = response.json()
            
            # Check if we need to redirect
            redirect_after_login = request.cookies.get("redirect_after_login")
            if redirect_after_login:
                response = RedirectResponse(
                    url=f"{redirect_after_login}?access_token={token_data['access_token']}"
                )
                response.delete_cookie(key="redirect_after_login")
                return response
            
            return token_data
            
    except Exception as e:
        logger.error(f"Error in Auth0 callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with Auth0: {str(e)}"
        )

@router.get("/logout")
async def logout():
    """Logout from Auth0"""
    return_to = "http://localhost:8000"
    logout_url = f"https://{settings.AUTH0_DOMAIN}/v2/logout?client_id={settings.AUTH0_CLIENT_ID}&returnTo={return_to}"
    return RedirectResponse(url=logout_url) 