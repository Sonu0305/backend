from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str
    
    # Email Configuration (Resend - HTTP API)
    RESEND_API_KEY: Optional[str] = None
    
    # SMTP Configuration (Legacy - won't work on Render free tier)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str = "Password Reset Service"
    
    # Application
    FRONTEND_URL: str
    SECRET_KEY: str
    TOKEN_EXPIRATION_MINUTES: int = 30
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
