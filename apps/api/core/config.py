import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "DECEPTRIX API"
    API_V1_STR: str = "/api/v1"
    
    # SQLite local DB
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./deceptrix.db"
    
    # Local Storage for MVP
    STORAGE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")

settings = Settings()

# Ensure storage directory exists
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
