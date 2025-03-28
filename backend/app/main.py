from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, email

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered email management system API",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(email.router, prefix=f"{settings.API_V1_STR}/email", tags=["email"])

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": {
            "project_name": settings.PROJECT_NAME,
            "api_v1_str": settings.API_V1_STR,
            "auth0_domain": settings.AUTH0_DOMAIN,
            "cors_origins": settings.BACKEND_CORS_ORIGINS
        }
    } 