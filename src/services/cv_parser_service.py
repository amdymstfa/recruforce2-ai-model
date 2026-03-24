"""
CV Parser Service - Orchestrates CV parsing workflow.
Handles file upload, parsing, and data extraction.
"""

import os
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
        """Parse via UploadFile (Multipart)."""
        file_path = await self.file_handler.save_upload_file(file)
        return await self._process_parsing(file_path, file.filename, candidate_id)

    async def parse_cv_from_bytes(self, content: bytes, filename: str, candidate_id: int = None) -> Dict:
        """Parse via Raw Bytes (JSON Base64)."""
        upload_dir = Path("uploads/cvs")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename
        
        with open(file_path, "wb") as f:
            f.write(content)
            
        return await self._process_parsing(file_path, filename, candidate_id)

    async def _process_parsing(self, file_path: Path, filename: str, candidate_id: int = None) -> Dict:
        """Internal logic for parsing and saving."""
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
                request_payload={"filename": filename},
                response_payload=parsed_data,
                status="SUCCESS",
                model_version="1.0.0"
            )
            
            logger.info(f"CV parsed successfully - MongoDB ID: {mongo_doc_id}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"CV parsing failed: {e}")
            await self.mongodb_service.log_ai_operation(
                operation_type="CV_PARSING",
                candidate_id=candidate_id,
                request_payload={"filename": filename},
                response_payload={},
                status="ERROR",
                error_message=str(e)
            )
            raise
        finally:
            if file_path.exists():
                os.remove(file_path)


# Global instance
cv_parser_service = None

def get_cv_parser_service() -> CVParserService:
    global cv_parser_service
    if cv_parser_service is None:
        cv_parser_service = CVParserService()
    return cv_parser_service