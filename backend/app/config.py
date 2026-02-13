"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    ENCRYPTION_KEY: str
    
    # Proxmox
    PROXMOX_HOST: str
    PROXMOX_PORT: int = 8006
    PROXMOX_USER: str
    PROXMOX_TOKEN_NAME: str
    PROXMOX_TOKEN_VALUE: str
    PROXMOX_VERIFY_SSL: bool = False
    
    # Application
    CORS_ORIGINS: str = "http://localhost:5173"
    VM_SYNC_INTERVAL_MINUTES: int = 5
    LOG_LEVEL: str = "INFO"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
