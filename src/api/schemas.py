"""
Pydantic schemas for API request and response validation.
Defines all DTOs used by the FastAPI endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


# =====================================================
# CV Parsing Schemas
# =====================================================

class CVParseJSONRequest(BaseModel):
    """Request for CV parsing via JSON (Base64)."""
    candidate_id: Optional[int] = Field(None, description="PostgreSQL candidate ID")
    file_base64: str = Field(..., description="CV file content encoded in Base64")
    filename: str = Field("cv.pdf", description="Original filename with extension")

class ExperienceSchema(BaseModel):
    """Professional experience entry."""
    position: str
    company: str
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False


class EducationSchema(BaseModel):
    """Education entry."""
    degree: str
    institution: str
    field: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    years_obtained: Optional[int] = None


class SkillSchema(BaseModel):
    """Skill with proficiency level."""
    name: str
    type: str = Field(..., description="TECHNICAL, SOFT, or LANGUAGE")
    mastery_level: Optional[str] = None
    years_experience: Optional[int] = None


class LanguageSchema(BaseModel):
    """Language proficiency."""
    name: str
    level: str = Field(..., description="CEFR level: A1, A2, B1, B2, C1, C2, NATIVE")


class ParsedCVResponse(BaseModel):
    """Response from CV parsing."""
    candidate_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    
    experiences: List[ExperienceSchema] = []
    educations: List[EducationSchema] = []
    skills: List[SkillSchema] = []
    languages: List[LanguageSchema] = []
    
    raw_text: Optional[str] = None
    parsing_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    model_version: str = "1.0.0"
    parsed_at: datetime = Field(default_factory=datetime.now)
    parsed_cv_id: Optional[str] = None

    # Autorise l'utilisation de noms de champs commençant par model_
    model_config = ConfigDict(protected_namespaces=())


# =====================================================
# Matching Schemas
# =====================================================

class MatchingRequest(BaseModel):
    """Request for matching score calculation."""
    candidate_id: int = Field(..., gt=0, description="PostgreSQL candidate ID")
    job_offer_id: int = Field(..., gt=0, description="PostgreSQL job offer ID")


class MatchingScoreResponse(BaseModel):
    """Response with matching score between candidate and job offer."""
    candidate_id: int
    candidate_name: Optional[str] = None
    job_offer_id: int
    job_offer_title: Optional[str] = None
    matching_score: int = Field(..., ge=0, le=100, description="Score 0-100")
    is_qualified: bool
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    model_version: str = "1.0.0"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    model_config = ConfigDict(protected_namespaces=())


# =====================================================
# Prediction Schemas
# =====================================================

class PredictionRequest(BaseModel):
    """Request for success prediction."""
    candidate_id: int = Field(..., gt=0)
    job_offer_id: int = Field(..., gt=0)


class PredictionResponse(BaseModel):
    """Response with ML prediction for hiring success."""
    candidate_id: int
    job_offer_id: int
    matching_score: float = Field(..., ge=0.0, le=100.0)
    success_probability: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    main_factors: str
    recommendation: str
    model_version: str = "1.0.0"
    calculated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(protected_namespaces=())


# =====================================================
# MongoDB Log Schemas
# =====================================================

class AILogRequest(BaseModel):
    """AI operation log entry."""
    operation_type: str = Field(..., description="CV_PARSING, MATCHING_SCORE, PREDICTION")
    candidate_id: Optional[int] = None
    job_offer_id: Optional[int] = None
    application_id: Optional[int] = None
    request_payload: Dict[str, Any] = {}
    response_payload: Dict[str, Any] = {}
    http_status: int = 200
    status: str = Field(..., description="SUCCESS, FAILURE, TIMEOUT, ERROR")
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    model_version: Optional[str] = None
    endpoint: Optional[str] = None

    model_config = ConfigDict(protected_namespaces=())


# =====================================================
# Health Check Schemas
# =====================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "UP"
    service: str = "RecruForce2 AI Service"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.now)
    mongodb_connected: bool = False
    models_loaded: bool = False


# =====================================================
# Error Schemas
# =====================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)