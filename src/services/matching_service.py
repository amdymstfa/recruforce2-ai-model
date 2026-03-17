"""
Matching Service - Calculates matching score between candidate and job offer.
Communicates with backend API to fetch candidate/job data.
"""

from typing import Dict, Optional
import httpx
from src.models.matching_model import get_matching_model
from src.core.config import settings
from src.utils.logger import get_logger
from src.services.mongodb_service import get_mongodb_service

logger = get_logger()


class MatchingService:
    """Service for calculating candidate-job matching scores."""

    def __init__(self):
        self.matching_model = get_matching_model()
        self.mongodb_service = get_mongodb_service()
        self.backend_url = settings.backend_api_url
        self._token: Optional[str] = None

    async def _get_token(self) -> str:
        """Authenticate against backend and return JWT token."""
        if self._token:
            return self._token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.backend_url}/api/auth/login",
                json={
                    "email": settings.backend_api_email,
                    "password": settings.backend_api_password
                },
                timeout=10.0
            )
            response.raise_for_status()
            self._token = response.json()["accessToken"]
            logger.info("AI service authenticated against backend")
            return self._token

    async def _get_headers(self) -> Dict:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}"}

    async def fetch_candidate_data(self, candidate_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            try:
                headers = await self._get_headers()
                response = await client.get(
                    f"{self.backend_url}/api/candidates/{candidate_id}",
                    headers=headers,
                    timeout=10.0
                )
                if response.status_code == 401:
                    self._token = None  # Reset token and retry
                    headers = await self._get_headers()
                    response = await client.get(
                        f"{self.backend_url}/api/candidates/{candidate_id}",
                        headers=headers,
                        timeout=10.0
                    )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to fetch candidate {candidate_id}: {e}")
                raise

    async def fetch_job_offer_data(self, job_offer_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            try:
                headers = await self._get_headers()
                response = await client.get(
                    f"{self.backend_url}/api/job-offers/{job_offer_id}",
                    headers=headers,
                    timeout=10.0
                )
                if response.status_code == 401:
                    self._token = None
                    headers = await self._get_headers()
                    response = await client.get(
                        f"{self.backend_url}/api/job-offers/{job_offer_id}",
                        headers=headers,
                        timeout=10.0
                    )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to fetch job offer {job_offer_id}: {e}")
                raise

    async def calculate_matching_score(self, candidate_id: int,
                                       job_offer_id: int) -> Dict:
        logger.info(f"Calculating match: candidate={candidate_id}, job={job_offer_id}")
        try:
            candidate_data = await self.fetch_candidate_data(candidate_id)
            job_offer_data = await self.fetch_job_offer_data(job_offer_id)

            candidate_skills = [s['name'] for s in candidate_data.get('skills', [])]
            candidate_languages = [l['name'] for l in candidate_data.get('languages', [])]
            required_skills = [s['name'] for s in job_offer_data.get('requiredSkills', [])]

            candidate_input = {
                'skills': candidate_skills,
                'languages': candidate_languages,
                'total_experience_years': self._calculate_total_experience(
                    candidate_data.get('experiences', [])
                )
            }
            job_offer_input = {
                'required_skills': required_skills,
                'required_languages': [],
                'min_experience': job_offer_data.get('minExperience', 0),
                'max_experience': job_offer_data.get('maxExperience', 20)
            }

            matching_result = self.matching_model.calculate_matching_score(
                candidate_input, job_offer_input
            )

            matching_result['candidate_id'] = candidate_id
            matching_result['candidate_name'] = f"{candidate_data.get('firstName')} {candidate_data.get('lastName')}"
            matching_result['job_offer_id'] = job_offer_id
            matching_result['job_offer_title'] = job_offer_data.get('title')

            await self.mongodb_service.log_ai_operation(
                operation_type="MATCHING_SCORE",
                candidate_id=candidate_id,
                job_offer_id=job_offer_id,
                request_payload={"candidate_id": candidate_id, "job_offer_id": job_offer_id},
                response_payload=matching_result,
                status="SUCCESS",
                model_version="1.0.0"
            )

            logger.info(f"Matching calculated: {matching_result['matching_score']}/100")
            return matching_result

        except Exception as e:
            logger.error(f"Matching calculation failed: {e}")
            await self.mongodb_service.log_ai_operation(
                operation_type="MATCHING_SCORE",
                candidate_id=candidate_id,
                job_offer_id=job_offer_id,
                request_payload={"candidate_id": candidate_id, "job_offer_id": job_offer_id},
                response_payload={},
                status="ERROR",
                error_message=str(e)
            )
            raise

    def _calculate_total_experience(self, experiences: list) -> int:
        return len(experiences)


matching_service = None


def get_matching_service() -> MatchingService:
    global matching_service
    if matching_service is None:
        matching_service = MatchingService()
    return matching_service
