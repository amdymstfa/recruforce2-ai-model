"""
FastAPI endpoints for RecruForce2 AI Service.
Provides REST API for CV parsing, matching, and predictions.
"""

import base64
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body, Request
from typing import Optional
from src.api.schemas import (
    ParsedCVResponse, 
    MatchingRequest, 
    MatchingScoreResponse,
    PredictionRequest,
    PredictionResponse,
    HealthResponse,
    ErrorResponse,
    CVParseJSONRequest
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
    mongodb_service = get_mongodb_service()
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
        models_loaded=True
    )


# =====================================================
# CV Parsing - VERSION ULTRA ROBUSTE
# =====================================================

@router.post("/api/parse-cv", response_model=ParsedCVResponse, tags=["CV Parsing"])
async def parse_cv(request: Request):
    """
    Parse a CV file. 
    Détecte automatiquement si c'est du JSON (n8n) ou du Form-Data (Curl).
    """
    cv_parser_service = get_cv_parser_service()
    content_type = request.headers.get("content-type", "")

    try:
        # CAS 1 : n8n envoie du JSON (application/json)
        if "application/json" in content_type:
            data = await request.json()
            c_id = data.get("candidate_id")
            f_name = data.get("filename", "cv.pdf")
            f_base64 = data.get("file_base64")

            if not f_base64:
                raise HTTPException(status_code=400, detail="file_base64 est vide")

            logger.info(f"n8n JSON detecté pour candidat {c_id}")
            file_content = base64.b64decode(f_base64)
            result = await cv_parser_service.parse_cv_from_bytes(file_content, f_name, c_id)
            return ParsedCVResponse(**result)

        # CAS 2 : Curl ou Postman (multipart/form-data)
        else:
            form = await request.form()
            file_field = form.get("file")
            c_id = form.get("candidate_id")

            if file_field and isinstance(file_field, UploadFile):
                logger.info(f"Fichier Multipart detecté: {file_field.filename}")
                candidate_id_int = int(c_id) if c_id else None
                result = await cv_parser_service.parse_cv(file_field, candidate_id_int)
                return ParsedCVResponse(**result)

        raise HTTPException(status_code=400, detail="Format de requête non supporté")

    except Exception as e:
        logger.error(f"ERREUR CRITIQUE PARSING: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# Matching Score
# =====================================================

@router.post("/api/match-score", response_model=MatchingScoreResponse, tags=["Matching"])
async def calculate_matching_score(request: MatchingRequest):
    try:
        logger.info(f"Calculating match: candidate={request.candidate_id}, job={request.job_offer_id}")
        matching_service = get_matching_service()
        result = await matching_service.calculate_matching_score(
            request.candidate_id,
            request.job_offer_id
        )
        return MatchingScoreResponse(**result)
    except Exception as e:
        logger.error(f"Matching calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# ML Prediction
# =====================================================

@router.post("/api/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_success(request: PredictionRequest):
    try:
        logger.info(f"Making prediction: candidate={request.candidate_id}, job={request.job_offer_id}")
        prediction_service = get_prediction_service()
        result = await prediction_service.predict_success(
            request.candidate_id,
            request.job_offer_id
        )
        return PredictionResponse(**result)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", tags=["Root"])
async def root():
    return {"service": settings.app_name, "version": settings.app_version, "status": "running"}


@router.get("/api/config", tags=["Configuration"])
async def get_config():
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "matching_threshold": settings.matching_threshold
    }