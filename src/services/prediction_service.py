"""
Prediction Service - ML predictions for hiring success.
"""

from typing import Dict
from src.models.prediction_model import get_prediction_model
from src.services.matching_service import get_matching_service
from src.utils.logger import get_logger
from src.services.mongodb_service import get_mongodb_service

logger = get_logger()


class PredictionService:
    """Service for ML-based hiring success predictions."""
    
    def __init__(self):
        self.prediction_model = get_prediction_model()
        self.matching_service = get_matching_service()
        self.mongodb_service = get_mongodb_service()
    
    async def predict_success(self, candidate_id: int, job_offer_id: int) -> Dict:
        """
        Predict hiring success probability.
        
        Args:
            candidate_id: Candidate ID
            job_offer_id: Job offer ID
            
        Returns:
            Prediction result with probability and recommendation
        """
        logger.info(f"Predicting success: candidate={candidate_id}, job={job_offer_id}")
        
        try:
            # First, calculate matching score
            matching_result = await self.matching_service.calculate_matching_score(
                candidate_id, job_offer_id
            )
            
            matching_score = matching_result['matching_score']
            
            # Fetch candidate and job data
            candidate_data = await self.matching_service.fetch_candidate_data(candidate_id)
            job_offer_data = await self.matching_service.fetch_job_offer_data(job_offer_id)
            
            # Prepare data for prediction
            candidate_input = {
                'skills': [s['name'] for s in candidate_data.get('skills', [])],
                'languages': [l['name'] for l in candidate_data.get('languages', [])],
                'educations': candidate_data.get('educations', []),
                'total_experience_years': len(candidate_data.get('experiences', []))
            }
            
            job_offer_input = {
                'required_skills': [s['name'] for s in job_offer_data.get('requiredSkills', [])],
                'required_languages': [],
                'min_experience': job_offer_data.get('minExperience', 0),
                'max_experience': job_offer_data.get('maxExperience', 20)
            }
            
            # Make prediction
            prediction_result = self.prediction_model.predict_success(
                candidate_input,
                job_offer_input,
                matching_score
            )
            
            # Add IDs
            prediction_result['candidate_id'] = candidate_id
            prediction_result['job_offer_id'] = job_offer_id
            
            # Log to MongoDB
            await self.mongodb_service.log_ai_operation(
                operation_type="PREDICTION",
                candidate_id=candidate_id,
                job_offer_id=job_offer_id,
                request_payload={
                    "candidate_id": candidate_id,
                    "job_offer_id": job_offer_id
                },
                response_payload=prediction_result,
                status="SUCCESS",
                model_version="1.0.0"
            )
            
            logger.info(f"Prediction: {prediction_result['success_probability']:.2%} success")
            return prediction_result
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            
            await self.mongodb_service.log_ai_operation(
                operation_type="PREDICTION",
                candidate_id=candidate_id,
                job_offer_id=job_offer_id,
                request_payload={
                    "candidate_id": candidate_id,
                    "job_offer_id": job_offer_id
                },
                response_payload={},
                status="ERROR",
                error_message=str(e)
            )
            
            raise


# Global instance
prediction_service = None


def get_prediction_service() -> PredictionService:
    """Get prediction service instance."""
    global prediction_service
    if prediction_service is None:
        prediction_service = PredictionService()
    return prediction_service