"""
MongoDB Service - Handles AI logs and parsed CV storage in MongoDB.
"""

from typing import Dict, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings
from src.utils.logger import get_logger

logger = get_logger()


class MongoDBService:
    """Service for MongoDB operations (AI logs and parsed CVs)."""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
    
    async def connect(self):
        """Connect to MongoDB."""
        try:
            connection_string = f"mongodb://{settings.mongodb_host}:{settings.mongodb_port}"
            self.client = AsyncIOMotorClient(connection_string)
            self.db = self.client[settings.mongodb_database]
            
            # Test connection
            await self.client.admin.command('ping')
            self.connected = True
            
            logger.info(f"Connected to MongoDB: {settings.mongodb_database}")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            self.connected = False
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("Disconnected from MongoDB")
    
    async def save_parsed_cv(self, parsed_data: Dict) -> str:
        """
        Save parsed CV data to MongoDB.
        
        Args:
            parsed_data: Parsed CV data
            
        Returns:
            MongoDB document ID
        """
        if not self.connected:
            await self.connect()
        
        collection = self.db[settings.mongodb_collection_parsed_cvs]
        
        # Add timestamp
        parsed_data['parsed_at'] = datetime.now()
        
        # Insert document
        result = await collection.insert_one(parsed_data)
        
        logger.info(f"Parsed CV saved to MongoDB: {result.inserted_id}")
        return result.inserted_id
    
    async def log_ai_operation(self,
                              operation_type: str,
                              candidate_id: Optional[int] = None,
                              job_offer_id: Optional[int] = None,
                              application_id: Optional[int] = None,
                              request_payload: Dict = None,
                              response_payload: Dict = None,
                              status: str = "SUCCESS",
                              error_message: Optional[str] = None,
                              duration_ms: Optional[int] = None,
                              model_version: Optional[str] = None,
                              endpoint: Optional[str] = None):
        """
        Log AI operation to MongoDB.
        
        Args:
            operation_type: Type of operation (CV_PARSING, MATCHING_SCORE, PREDICTION)
            candidate_id: Candidate ID (if applicable)
            job_offer_id: Job offer ID (if applicable)
            application_id: Application ID (if applicable)
            request_payload: Request data
            response_payload: Response data
            status: Operation status (SUCCESS, ERROR, TIMEOUT)
            error_message: Error message (if failed)
            duration_ms: Duration in milliseconds
            model_version: Model version used
            endpoint: API endpoint called
        """
        if not self.connected:
            await self.connect()
        
        collection = self.db[settings.mongodb_collection_logs]
        
        log_entry = {
            "operation_type": operation_type,
            "candidate_id": candidate_id,
            "job_offer_id": job_offer_id,
            "application_id": application_id,
            "request_payload": request_payload or {},
            "response_payload": response_payload or {},
            "http_status": 200 if status == "SUCCESS" else 500,
            "status": status,
            "error_message": error_message,
            "duration_ms": duration_ms,
            "model_version": model_version,
            "endpoint": endpoint,
            "called_at": datetime.now()
        }
        
        await collection.insert_one(log_entry)
        logger.debug(f"AI operation logged: {operation_type}")
    
    async def get_parsed_cv(self, candidate_id: int) -> Optional[Dict]:
        """
        Retrieve parsed CV from MongoDB.
        
        Args:
            candidate_id: Candidate ID
            
        Returns:
            Parsed CV data or None
        """
        if not self.connected:
            await self.connect()
        
        collection = self.db[settings.mongodb_collection_parsed_cvs]
        document = await collection.find_one({"candidate_id": candidate_id})
        
        return document


# Global instance
mongodb_service = None


def get_mongodb_service() -> MongoDBService:
    """Get MongoDB service instance."""
    global mongodb_service
    if mongodb_service is None:
        mongodb_service = MongoDBService()
    return mongodb_service