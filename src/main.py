"""
RecruForce2 AI Service - Main FastAPI Application.
Entry point for the AI microservice.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.api.endpoints import router
from src.core.config import settings
from src.utils.logger import get_logger
from src.services.mongodb_service import get_mongodb_service

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Connect to MongoDB
    mongodb_service = get_mongodb_service()
    await mongodb_service.connect()
    
    logger.info(f"Server running on {settings.host}:{settings.port}")
    logger.info(f"API docs available at http://{settings.host}:{settings.port}/docs")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await mongodb_service.disconnect()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    RecruForce2 AI Microservice provides intelligent CV parsing, 
    candidate-job matching, and hiring success predictions.
    
    ## Features
    
    * **CV Parsing**: Extract structured data from PDF and DOCX resumes
    * **Matching Algorithm**: Calculate compatibility scores between candidates and job offers
    * **ML Predictions**: Predict hiring success probability using machine learning
    * **MongoDB Integration**: Store AI logs and parsed CV data
    
    ## Usage
    
    1. Upload a CV to `/api/parse-cv` to extract structured data
    2. Calculate matching score with `/api/match-score`
    3. Get hiring predictions with `/api/predict`
    
    All endpoints are documented below with interactive testing capabilities.
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "Internal Server Error",
        "message": str(exc) if settings.debug else "An unexpected error occurred"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )