from pydantic_settings import BaseSettings
from typing import List, Union
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "Copro App"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Copro App API"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://copro:copro_password@db:5432/copro_app"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 heures pour faciliter le développement
    
    # CORS - can be a JSON string or list
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173"]
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from string or return list"""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            try:
                return json.loads(self.BACKEND_CORS_ORIGINS)
            except json.JSONDecodeError:
                # If not JSON, treat as comma-separated
                return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return self.BACKEND_CORS_ORIGINS
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

