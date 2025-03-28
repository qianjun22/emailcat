from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt, jwe
from .config import settings
import httpx
import json

security = HTTPBearer()

def get_token_auth_header(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Obtains the Access Token from the Authorization Header"""
    return credentials.credentials

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Get the current user from the JWT token.
    For encrypted tokens, we'll need to get the user info from Auth0's userinfo endpoint.
    """
    try:
        token = get_token_auth_header(credentials)
        
        # For development, we'll use a mock user
        if settings.AUTH0_DOMAIN == "your-tenant.auth0.com":
            return {
                "sub": "mock-user-id",
                "email": "test@example.com",
                "name": "Test User"
            }
        
        # Get user info from Auth0's userinfo endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://{settings.AUTH0_DOMAIN}/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return response.json()
            
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) 