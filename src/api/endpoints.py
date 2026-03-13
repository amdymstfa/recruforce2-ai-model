"""
FastAPI endpoints for RecruForce2 AI Service.
Provides REST API for CV parsing, matching, and predictions.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional
from src.api.schemas import (
    ParsedCVResponse, 
    MatchingRequest, 
    MatchingScoreResponse,
    PredictionRequest,
    PredictionResponse,
    HealthResponse,
    ErrorResponse
)
from src.services.cv_parser_service import get_cv_parser_service
from src.services.matching_service import get_matching_service
from src.services.prediction_service import get_prediction_service
from src.services.mongodb_service import get_mongodb_service
from src.utils.logger import get_logger
from src.core.config import settings

logger = get_logger()
router = APIRouter()


# =====================================================
# Health Check
# =====================================================

@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns service status and connectivity.
    """
    mongodb_service = get_mongodb_service()
    
    # Check MongoDB connection
    mongodb_connected = mongodb_service.connected
    if not mongodb_connected:
        try:
            await mongodb_service.connect()
            mongodb_connected = mongodb_service.connected
        except:
            mongodb_connected = False
    
    return HealthResponse(
        status="UP",
        service=settings.app_name,
        version=settings.app_version,
        mongodb_connected=mongodb_connected,
        models_loaded=True  # TODO: Check if models are actually loaded
    )


# =====================================================
# CV Parsing
# =====================================================

@router.post("/api/parse-cv", response_model=ParsedCVResponse, tags=["CV Parsing"])
async def parse_cv(
    file: UploadFile = File(..., description="CV file (PDF or DOCX)"),
    candidate_id: Optional[int] = Query(None, description="PostgreSQL candidate ID")
):
    """
    Parse a CV file and extract structured data.
    
    - **file**: CV file in PDF or DOCX format
    - **candidate_id**: Optional candidate ID from PostgreSQL database
    
    Returns parsed candidate information including:
    - Personal information (name, email, phone)
    - Work experiences
    - Education
    - Skills
    - Languages
    """
    try:
        logger.info(f"Received CV parsing request: {file.filename}")
        
        cv_parser_service = get_cv_parser_service()
        result = await cv_parser_service.parse_cv(file, candidate_id)
        
        return ParsedCVResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"CV parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"CV parsing failed: {str(e)}")


# =====================================================
# Matching Score
# =====================================================

@router.post("/api/match-score", response_model=MatchingScoreResponse, tags=["Matching"])
async def calculate_matching_score(request: MatchingRequest):
    """
    Calculate matching score between a candidate and a job offer.
    
    - **candidate_id**: PostgreSQL candidate ID
    - **job_offer_id**: PostgreSQL job offer ID
    
    Returns:
    - Matching score (0-100)
    - Matched skills
    - Missing skills
    - Qualification status
    """
    try:
        logger.info(f"Calculating match: candidate={request.candidate_id}, job={request.job_offer_id}")
        
        matching_service = get_matching_service()
        result = await matching_service.calculate_matching_score(
            request.candidate_id,
            request.job_offer_id
        )
        
        return MatchingScoreResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Matching calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")


# =====================================================
# ML Prediction
# =====================================================

@router.post("/api/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_success(request: PredictionRequest):
    """
    Predict hiring success probability using ML model.
    
    - **candidate_id**: PostgreSQL candidate ID
    - **job_offer_id**: PostgreSQL job offer ID
    
    Returns:
    - Success probability (0.0 - 1.0)
    - Matching score
    - Confidence level
    - Main factors influencing the prediction
    - Hiring recommendation
    """
    try:
        logger.info(f"Making prediction: candidate={request.candidate_id}, job={request.job_offer_id}")
        
        prediction_service = get_prediction_service()
        result = await prediction_service.predict_success(
            request.candidate_id,
            request.job_offer_id
        )
        
        return PredictionResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# =====================================================
# Utility Endpoints
# =====================================================

@router.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@router.get("/api/config", tags=["Configuration"])
async def get_config():
    """Get API configuration."""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "max_file_size_mb": settings.max_file_size_mb,
        "allowed_extensions": settings.allowed_extensions,
        "matching_threshold": settings.matching_threshold
    }