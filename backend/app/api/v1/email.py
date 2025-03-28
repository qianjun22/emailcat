from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Header, Body
from fastapi.responses import RedirectResponse, JSONResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.auth import get_current_user
from app.core.config import settings
import json
import logging
import secrets
from typing import Optional, List, Dict

router = APIRouter()
logger = logging.getLogger(__name__)

GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def create_flow():
    """Create a new OAuth 2.0 flow instance"""
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=GMAIL_SCOPES
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    return flow

@router.get("/google/connect")
async def gmail_connect(request: Request, response: Response):
    """One-click Gmail connection flow that handles Auth0 automatically"""
    try:
        # First, redirect to Auth0 login with proper API prefix
        auth_url = f"{request.base_url.scheme}://{request.base_url.netloc}{settings.API_V1_STR}/auth/login?redirect_after_login={request.base_url.scheme}://{request.base_url.netloc}{settings.API_V1_STR}/email/google/auth"
        logger.info(f"Redirecting to Auth0 login: {auth_url}")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Error in Gmail connect: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Failed to start Gmail connection flow"}
        )

@router.get("/google/auth")
async def gmail_auth(
    request: Request,
    response: Response,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = None,
    access_token: Optional[str] = None  # For Auth0 redirect
):
    """Start Gmail OAuth flow"""
    try:
        # Check for token in various places
        auth_token = None
        if authorization:
            auth_token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        elif token:
            auth_token = token
        elif access_token:
            auth_token = access_token
        elif request.cookies.get("auth0_token"):
            auth_token = request.cookies.get("auth0_token")
            
        if not auth_token:
            logger.error("No authorization token provided")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "No authorization token provided"}
            )
        
        # Create flow and generate state
        flow = create_flow()
        state = secrets.token_urlsafe(32)
        
        # Generate authorization URL with state
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',  # Force consent screen to appear
            state=state  # Include state parameter for security
        )
        
        logger.info(f"Generated authorization URL: {authorization_url}")
        logger.info(f"Generated state: {state}")
        
        # Create response with redirect
        response = RedirectResponse(url=authorization_url)
        
        # Set cookies with proper settings
        response.set_cookie(
            key="oauth_state",
            value=state,
            httponly=True,
            path="/",
            max_age=600  # 10 minutes
        )
        
        response.set_cookie(
            key="auth0_token",
            value=auth_token,
            httponly=True,
            path="/",
            max_age=600  # 10 minutes
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in Gmail auth: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Failed to start Gmail authentication",
                "detail": str(e)
            }
        )

@router.post("/gmail/messages")
async def list_messages(
    max_results: int = 10,
    credentials: Dict = Body(None)
):
    """List Gmail messages"""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Gmail credentials not provided"
            )
        
        # Extract credentials from the nested structure
        gmail_credentials = credentials.get('credentials')
        if not gmail_credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Gmail credentials not found in request"
            )
        
        # Create Gmail API service
        service = await get_gmail_service(gmail_credentials)
        
        # List messages
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        
        # Get detailed message data
        detailed_messages = []
        for msg in messages:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            # Extract headers
            headers = message.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            
            detailed_messages.append({
                'id': message['id'],
                'subject': subject,
                'from': sender,
                'date': date,
                'snippet': message.get('snippet', ''),
                'labelIds': message.get('labelIds', [])
            })
        
        return {
            "messages": detailed_messages,
            "nextPageToken": results.get('nextPageToken'),
            "resultSizeEstimate": results.get('resultSizeEstimate')
        }
        
    except HttpError as e:
        logger.error(f"Gmail API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gmail API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error listing Gmail messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list Gmail messages: {str(e)}"
        )

@router.get("/google/callback")
async def gmail_callback(
    request: Request,
    response: Response,
    code: str,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """Handle Gmail OAuth callback"""
    try:
        logger.info("Received Gmail OAuth callback")
        logger.info(f"Received state: {state}")
        logger.info(f"Cookies: {request.cookies}")
        
        # Check for OAuth errors
        if error:
            logger.error(f"OAuth error: {error}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "OAuth error", "detail": error}
            )
        
        # Verify state
        cookie_state = request.cookies.get("oauth_state")
        logger.info(f"Cookie state: {cookie_state}")
        
        if not state or not cookie_state:
            logger.error("Missing state parameter")
            logger.error(f"State from URL: {state}")
            logger.error(f"State from cookie: {cookie_state}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Missing state parameter"}
            )
            
        if state != cookie_state:
            logger.error(f"State mismatch. Expected: {cookie_state}, Got: {state}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid state parameter"}
            )
        
        # Get Auth0 token from cookie
        auth0_token = request.cookies.get("auth0_token")
        if not auth0_token:
            logger.error("No Auth0 token found in cookies")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "No Auth0 token found"}
            )
        
        # Exchange code for tokens
        flow = create_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Create response data
        response_data = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "scopes": credentials.scopes
        }
        
        # Create HTML response with test URL
        test_url = f"{request.base_url.scheme}://{request.base_url.netloc}{settings.API_V1_STR}/email/gmail/messages"
        html_content = f"""
        <html>
            <head>
                <title>Gmail Authentication Success</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .container {{ max-width: 1200px; margin: 0 auto; }}
                    .success {{ color: green; }}
                    .test-section {{ margin-top: 20px; padding: 20px; border: 1px solid #ccc; border-radius: 5px; }}
                    pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                    .messages-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    .messages-table th, .messages-table td {{ 
                        padding: 12px; 
                        text-align: left; 
                        border-bottom: 1px solid #ddd;
                    }}
                    .messages-table th {{ 
                        background-color: #f8f9fa;
                        border-top: 2px solid #dee2e6;
                    }}
                    .messages-table tr:hover {{ background-color: #f5f5f5; }}
                    .snippet {{ 
                        color: #666;
                        max-width: 300px;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }}
                    .date {{ color: #666; }}
                    .loading {{ 
                        text-align: center; 
                        padding: 20px;
                        display: none;
                    }}
                    .error-message {{
                        color: red;
                        padding: 10px;
                        display: none;
                    }}
                    #messagesContainer {{ display: none; }}
                    .refresh-button {{
                        background-color: #4CAF50;
                        color: white;
                        padding: 10px 20px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        margin-top: 10px;
                    }}
                    .refresh-button:hover {{
                        background-color: #45a049;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="success">Gmail Authentication Successful!</h1>
                    <p>Your Gmail account has been successfully connected.</p>
                    
                    <div class="test-section">
                        <h2>Your Gmail Messages</h2>
                        <button onclick="testGmailMessages()" class="refresh-button">Load Messages</button>
                        
                        <div id="loadingMessages" class="loading">
                            Loading messages...
                        </div>
                        
                        <div id="errorMessage" class="error-message"></div>
                        
                        <div id="messagesContainer">
                            <table class="messages-table">
                                <thead>
                                    <tr>
                                        <th>From</th>
                                        <th>Subject</th>
                                        <th>Preview</th>
                                        <th>Date</th>
                                    </tr>
                                </thead>
                                <tbody id="messagesTableBody">
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <script>
                function formatDate(dateStr) {{
                    const date = new Date(dateStr);
                    return date.toLocaleString();
                }}
                
                function testGmailMessages() {{
                    const loadingDiv = document.getElementById('loadingMessages');
                    const errorDiv = document.getElementById('errorMessage');
                    const messagesContainer = document.getElementById('messagesContainer');
                    const tableBody = document.getElementById('messagesTableBody');
                    
                    loadingDiv.style.display = 'block';
                    errorDiv.style.display = 'none';
                    messagesContainer.style.display = 'none';
                    
                    fetch("{test_url}", {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            credentials: {json.dumps(response_data)}
                        }})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        loadingDiv.style.display = 'none';
                        messagesContainer.style.display = 'block';
                        
                        // Clear existing messages
                        tableBody.innerHTML = '';
                        
                        // Add each message to the table
                        data.messages.forEach(message => {{
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>${{message.from}}</td>
                                <td><strong>${{message.subject}}</strong></td>
                                <td class="snippet">${{message.snippet}}</td>
                                <td class="date">${{formatDate(message.date)}}</td>
                            `;
                            tableBody.appendChild(row);
                        }});
                        
                        console.log('Gmail Messages:', data);
                    }})
                    .catch(error => {{
                        loadingDiv.style.display = 'none';
                        errorDiv.style.display = 'block';
                        errorDiv.textContent = 'Error loading messages: ' + error;
                        console.error('Error:', error);
                    }});
                }}
                
                // Load messages automatically when the page loads
                window.onload = testGmailMessages;
                </script>
            </body>
        </html>
        """
        
        # Create response with proper cookie cleanup
        response = Response(content=html_content, media_type="text/html")
        response.delete_cookie(key="oauth_state", path="/")
        response.delete_cookie(key="auth0_token", path="/")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in Gmail callback: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Failed to complete Gmail authentication",
                "detail": str(e)
            }
        )

async def get_gmail_service(credentials_dict: Dict):
    """Create Gmail API service instance"""
    try:
        credentials = Credentials(
            token=credentials_dict.get('access_token'),
            refresh_token=credentials_dict.get('refresh_token'),
            token_uri=credentials_dict.get('token_uri'),
            client_id=credentials_dict.get('client_id'),
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=credentials_dict.get('scopes')
        )
        
        return build('gmail', 'v1', credentials=credentials)
    except Exception as e:
        logger.error(f"Error creating Gmail service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Gmail service"
        ) 