"""Centralized configuration management using Pydantic Settings.

This module provides application-wide configuration loaded from environment
variables and .env files. All settings are validated using Pydantic v2.

Usage:
    from src.config import settings

    print(settings.gemini_api_key)
    print(settings.qdrant_url)
"""

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        gemini_api_key: Google Gemini API key for embeddings
        qdrant_url: Qdrant vector database URL
        qdrant_api_key: Optional Qdrant API key (for cloud)
        database_path: Path to SQLite database file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        debug: Enable debug mode
        mcp_server_host: Host for MCP servers
        mcp_server_port: Base port for MCP servers
        embedding_model: Gemini embedding model name
        embedding_dimension: Embedding vector dimension
        chunk_size: Default chunk size for text splitting
        chunk_overlap: Default chunk overlap for text splitting
    """

    # Google Gemini API
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key for embeddings",
    )

    # Qdrant Configuration
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant vector database URL",
    )
    qdrant_api_key: str | None = Field(
        default=None,
        description="Optional Qdrant API key (for cloud deployment)",
    )

    # Database
    database_path: str = Field(
        default="./data/shop.db",
        description="Path to SQLite database file",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Application
    debug: bool = Field(
        default=False,
        description="Enable debug mode for verbose logging",
    )

    # MCP Server Configuration
    mcp_server_host: str = Field(
        default="localhost",
        description="Host for MCP servers",
    )
    mcp_server_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Base port for MCP servers",
    )

    # RAG Configuration
    embedding_model: str = Field(
        default="gemini-embedding-001",
        description="Gemini embedding model name",
    )
    embedding_dimension: int = Field(
        default=3072,
        ge=1,
        description="Embedding vector dimension",
    )
    chunk_size: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="Default chunk size for text splitting (in tokens)",
    )
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=500,
        description="Default chunk overlap for text splitting (in tokens)",
    )

    # Search Configuration
    default_top_k: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Default number of results for similarity search",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @field_validator("database_path")
    @classmethod
    def validate_database_path(cls, v: str) -> str:
        """Ensure database directory exists."""
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: int, info) -> int:
        """Ensure chunk overlap is less than chunk size."""
        chunk_size = info.data.get("chunk_size", 500)
        if v >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance (cached for performance)
    """
    return Settings()


# Global settings instance
settings = get_settings()


def configure_logging() -> None:
    """Configure logging based on settings.

    Sets up the root logger with the configured log level and format.
    """
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.debug else logging.WARNING
    )
