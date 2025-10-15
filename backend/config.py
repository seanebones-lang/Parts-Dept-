from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "parts-dept-system"
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Neo4j
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str = "neo4j"
    
    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection_name: str = "parts_dept_docs"
    
    # LLM Configuration
    ollama_base_url: str = "http://localhost:11434"
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    
    llama_model: str = "llama3.2:latest"
    claude_model: str = "claude-3-5-sonnet-20241022"
    mistral_model: str = "mistral-large-latest"
    
    # Email
    imap_host: str
    imap_port: int = 993
    imap_user: str
    imap_password: str
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    email_from: str
    
    # Database
    database_url: str
    
    # Redis & Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    
    # Payment
    stripe_api_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    # System Configuration
    confidence_threshold: float = 0.75
    max_email_batch_size: int = 50
    invoice_storage_path: str = "/app/data/invoices"


settings = Settings()

