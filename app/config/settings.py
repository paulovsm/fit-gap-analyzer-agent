from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Google/Gemini Configuration
    google_api_key: str
    gemini_model: str = "gemini-2.5-flash-thinking-exp-01-21"
    
    # Firebase Configuration
    firebase_project_id: str
    google_application_credentials: Optional[str] = None
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Firestore Collections
    presentation_collection: str = "presentation_transcriptions"
    meeting_collection: str = "transcriptions"
    requirements_collection: str = "requirements"
    
    # CrewAI Configuration
    crew_verbose: bool = True
    crew_memory: bool = True
    
    # File Upload Configuration
    uploads_dir: str = "./uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".xlsx", ".xls", ".csv"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
