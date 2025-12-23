"""Centralized configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Google Gemini API
    gemini_api_key: str = ""

    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    # Database
    database_path: str = "./data/shop.db"

    # Logging
    log_level: str = "INFO"

    # Application
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
