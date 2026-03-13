"""
CV Parser Service - Orchestrates CV parsing workflow.
Handles file upload, parsing, and data extraction.
"""

from pathlib import Path
from typing import Dict
from fastapi import UploadFile
from src.models.resume_parser_model import get_parser_model
from src.utils.file_handler import get_file_handler
from src.utils.validators import validate_candidate_data
from src.utils.logger import get_logger
from src.services.mongodb_service import get_mongodb_service

logger = get_logger()


class CVParserService:
    """Service for parsing CV files and extracting structured data."""
    
    def __init__(self):
        self.parser_model = get_parser_model()
        self.file_handler = get_file_handler()
        self.mongodb_service = get_mongodb_service()
    
    async def parse_cv(self, file: UploadFile, candidate_id: int = None) -> Dict:
        """
        Parse CV file and extract structured data.
        
        Args:
            file: Uploaded CV file (PDF or DOCX)
            candidate_id: Optional PostgreSQL candidate ID
            
        Returns:
            Parsed CV data
        """
        logger.info(f"Starting CV parsing for file: {file.filename}")
        
        # Save uploaded file
        file_path = await self.file_handler.save_upload_file(file)
        
        try:
            # Parse CV
            parsed_data = self.parser_model.parse_cv(file_path)
            
            # Add candidate ID if provided
            if candidate_id:
                parsed_data['candidate_id'] = candidate_id
            
            # Validate data
            parsed_data = validate_candidate_data(parsed_data)
            
            # Save to MongoDB
            mongo_doc_id = await self.mongodb_service.save_parsed_cv(parsed_data)
            parsed_data['parsed_cv_id'] = str(mongo_doc_id)
            
            # Log operation to MongoDB
            await self.mongodb_service.log_ai_operation(
                operation_type="CV_PARSING",
                candidate_id=candidate_id,
                request_payload={"filename": file.filename},
                response_payload=parsed_data,
                status="SUCCESS",
                model_version="1.0.0"
            )
            
            logger.info(f"CV parsed successfully - MongoDB ID: {mongo_doc_id}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"CV parsing failed: {e}")
            
            # Log error to MongoDB
            await self.mongodb_service.log_ai_operation(
                operation_type="CV_PARSING",
                candidate_id=candidate_id,
                request_payload={"filename": file.filename},
                response_payload={},
                status="ERROR",
                error_message=str(e)
            )
            
            raise
        
        finally:
            # Cleanup uploaded file
            self.file_handler.delete_file(file_path)


# Global instance
cv_parser_service = None


def get_cv_parser_service() -> CVParserService:
    """Get CV parser service instance."""
    global cv_parser_service
    if cv_parser_service is None:
        cv_parser_service = CVParserService()
    return cv_parser_service