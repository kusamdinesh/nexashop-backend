from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str
    MONGO_URL: str
    MONGO_DB: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REDIS_URL: str = "redis://localhost:6379"
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@nexashop.com"
    FROM_NAME: str = "NexaShop"
    ADMIN_EMAIL: str = "admin@nexashop.com"

    class Config:
        env_file = ".env"

settings = Settings()