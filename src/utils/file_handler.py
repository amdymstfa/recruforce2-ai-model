"""
File handling utilities for CV uploads and processing.
Supports PDF and DOCX file validation and storage.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from src.core.config import settings
from src.utils.logger import get_logger

logger = get_logger()


class FileHandler:
    """Handles file upload, validation, and storage."""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = settings.max_file_size_mb * 1024 * 1024
        self.allowed_extensions = settings.allowed_extensions
    
    def validate_file(self, file: UploadFile) -> bool:
        """
        Validate uploaded file (extension and size).
        
        Args:
            file: Uploaded file from FastAPI
            
        Returns:
            True if valid
            
        Raises:
            HTTPException: If validation fails
        """
        # Check file extension
        file_ext = Path(file.filename).suffix.lower().replace('.', '')
        if file_ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {', '.join(self.allowed_extensions)}"
            )
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > self.max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.max_file_size_mb}MB"
            )
        
        logger.info(f"File validated: {file.filename} ({file_size} bytes)")
        return True
    
    async def save_upload_file(self, file: UploadFile) -> Path:
        """
        Save uploaded file to disk.
        
        Args:
            file: Uploaded file from FastAPI
            
        Returns:
            Path to saved file
        """
        self.validate_file(file)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        safe_filename = f"{os.urandom(16).hex()}{file_ext}"
        file_path = self.upload_dir / safe_filename
        
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved: {file_path}")
        return file_path
    
    def delete_file(self, file_path: Path) -> bool:
        """
        Delete a file from disk.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deleted, False if file doesn't exist
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def cleanup_old_files(self, days: int = 7):
        """
        Delete files older than specified days.
        
        Args:
            days: Files older than this will be deleted
        """
        import time
        current_time = time.time()
        count = 0
        
        for file_path in self.upload_dir.iterdir():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > (days * 86400):  # days to seconds
                    self.delete_file(file_path)
                    count += 1
        
        logger.info(f"Cleanup: {count} old files deleted")


# Global instance
file_handler = FileHandler()


def get_file_handler() -> FileHandler:
    """Get file handler instance."""
    return file_handler