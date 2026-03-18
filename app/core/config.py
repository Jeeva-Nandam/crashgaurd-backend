from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB
    # MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_URL: str = "mongodb+srv://jeevanandam2430_db_user:JDqrTmGyRivwSdJl@cluster0.hdtzykb.mongodb.net/crash-app?retryWrites=true&w=majority"
    DATABASE_NAME: str = "crash-app"
    
    # JWT
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Email (Resend)
    RESEND_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@crashguard.app"

    # OTP
    OTP_EXPIRE_MINUTES: int = 10

    # App
    APP_NAME: str = "CrashGuard"
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
