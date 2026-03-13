"""
API module - FastAPI endpoints and schemas.
"""

from src.api.endpoints import router
from src.api.schemas import (
    ParsedCVResponse,
    MatchingRequest,
    MatchingScoreResponse,
    PredictionRequest,
    PredictionResponse,
    HealthResponse,
    ErrorResponse
)

__all__ = [
    "router",
    "ParsedCVResponse",
    "MatchingRequest",
    "MatchingScoreResponse",
    "PredictionRequest",
    "PredictionResponse",
    "HealthResponse",
    "ErrorResponse"
]