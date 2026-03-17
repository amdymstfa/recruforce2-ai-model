from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
  """Application settings loaded from environment variables."""

  # Application
  app_name: str = "RecruForce2 AI Service"
  app_version: str = "1.0.0"
  debug: bool = True
  host: str = "0.0.0.0"
  port: int = 8000

  # MongoDB
  mongodb_host: str = "localhost"
  mongodb_port: int = 27017
  mongodb_database: str = "recruforce2_dev"
  mongodb_collection_logs: str = "ai_logs"
  mongodb_collection_parsed_cvs: str = "parsed_cvs"

  # Backend API
  backend_api_url: str = "http://localhost:8080"
  backend_api_email: str = "ai-service2@recruforce2.internal"
  backend_api_password: str = "AiService@2024!"

  # File Upload
  max_file_size_mb: int = 10
  allowed_extensions: List[str] = ["pdf", "docx", "doc"]
  upload_dir: str = "./uploads"

  # Logging
  log_level: str = "INFO"
  log_file: str = "./logs/ai_service.log"

  # ML Models
  models_dir: str = "./persistence/trained_models"
  matching_model_path: str = "./persistence/trained_models/matching_score_v1.pkl"

  # NLP
  spacy_model: str = "fr_core_news_md"

  # Thresholds
  matching_threshold: int = 60
  prediction_confidence_min: float = 0.5

  class Config:
    env_file = ".env"
    case_sensitive = False
    extra = "ignore"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
  """Get application settings."""
  return settings
# Already in Settings class — add these fields if not present
