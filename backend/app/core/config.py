from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "EmailCat"
    
    # Auth0 Settings
    AUTH0_DOMAIN: str
    AUTH0_AUDIENCE: str
    
    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    
    # Microsoft OAuth Settings
    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET: str
    
    # OpenAI Settings
    OPENAI_API_KEY: str
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 