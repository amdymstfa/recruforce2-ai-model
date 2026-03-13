"""
Matching Model - Calculates compatibility score between candidate and job offer.
Uses skill matching and experience alignment.
"""

from typing import Dict, List, Set
import pickle
from pathlib import Path
from src.core.config import settings
from src.utils.logger import get_logger

logger = get_logger()


class MatchingModel:
    """Model for calculating candidate-job offer matching scores."""
    
    def __init__(self):
        """Initialize matching model."""
        self.weights = {
            'skills': 0.5,
            'experience': 0.3,
            'languages': 0.2
        }
        logger.info("Matching model initialized")
    
    def calculate_skill_match(self, 
                             candidate_skills: List[str], 
                             required_skills: List[str]) -> float:
        """
        Calculate skill matching score.
        
        Args:
            candidate_skills: List of candidate's skills
            required_skills: List of required skills for the job
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not required_skills:
            return 1.0
        
        candidate_set = set(skill.lower() for skill in candidate_skills)
        required_set = set(skill.lower() for skill in required_skills)
        
        if not required_set:
            return 1.0
        
        matched = candidate_set.intersection(required_set)
        score = len(matched) / len(required_set)
        
        logger.debug(f"Skill match: {len(matched)}/{len(required_set)} = {score:.2f}")
        return score
    
    def calculate_experience_match(self, 
                                   candidate_years: int, 
                                   min_years: int, 
                                   max_years: int) -> float:
        """
        Calculate experience matching score.
        
        Args:
            candidate_years: Years of experience the candidate has
            min_years: Minimum required years
            max_years: Maximum required years
            
        Returns:
            Score between 0.0 and 1.0
        """
        if candidate_years >= min_years and candidate_years <= max_years:
            return 1.0
        elif candidate_years < min_years:
            # Below minimum - score decreases
            gap = min_years - candidate_years
            return max(0.0, 1.0 - (gap * 0.1))  # -10% per missing year
        else:
            # Above maximum - still good but slight penalty
            return 0.9
    
    def calculate_language_match(self, 
                                candidate_languages: List[str], 
                                required_languages: List[str]) -> float:
        """
        Calculate language matching score.
        
        Args:
            candidate_languages: Languages the candidate speaks
            required_languages: Required languages
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not required_languages:
            return 1.0
        
        candidate_set = set(lang.lower() for lang in candidate_languages)
        required_set = set(lang.lower() for lang in required_languages)
        
        matched = candidate_set.intersection(required_set)
        score = len(matched) / len(required_set)
        
        return score
    
    def calculate_matching_score(self, candidate_data: Dict, job_offer_data: Dict) -> Dict:
        """
        Calculate overall matching score between candidate and job offer.
        
        Args:
            candidate_data: Candidate information with skills, experience, languages
            job_offer_data: Job offer requirements
            
        Returns:
            Matching result with score and details
        """
        # Extract candidate data
        candidate_skills = candidate_data.get('skills', [])
        candidate_languages = candidate_data.get('languages', [])
        candidate_experience_years = candidate_data.get('total_experience_years', 0)
        
        # Extract job requirements
        required_skills = job_offer_data.get('required_skills', [])
        required_languages = job_offer_data.get('required_languages', [])
        min_experience = job_offer_data.get('min_experience', 0)
        max_experience = job_offer_data.get('max_experience', 20)
        
        # Calculate component scores
        skill_score = self.calculate_skill_match(candidate_skills, required_skills)
        experience_score = self.calculate_experience_match(
            candidate_experience_years, min_experience, max_experience
        )
        language_score = self.calculate_language_match(
            candidate_languages, required_languages
        )
        
        # Weighted overall score
        overall_score = (
            skill_score * self.weights['skills'] +
            experience_score * self.weights['experience'] +
            language_score * self.weights['languages']
        )
        
        # Convert to 0-100 scale
        final_score = int(overall_score * 100)
        
        # Determine matched and missing skills
        candidate_skill_set = set(s.lower() for s in candidate_skills)
        required_skill_set = set(s.lower() for s in required_skills)
        
        matched_skills = list(candidate_skill_set.intersection(required_skill_set))
        missing_skills = list(required_skill_set - candidate_skill_set)
        
        # Is qualified?
        is_qualified = final_score >= settings.matching_threshold
        
        result = {
            'matching_score': final_score,
            'is_qualified': is_qualified,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'skill_score': round(skill_score * 100, 2),
            'experience_score': round(experience_score * 100, 2),
            'language_score': round(language_score * 100, 2),
            'confidence': 0.85,  # Model confidence
            'model_version': '1.0.0'
        }
        
        logger.info(f"Matching calculated: {final_score}/100 - Qualified: {is_qualified}")
        return result
    
    def save_model(self, path: Path):
        """Save model to disk."""
        with open(path, 'wb') as f:
            pickle.dump(self, f)
        logger.info(f"Model saved to {path}")
    
    @staticmethod
    def load_model(path: Path) -> 'MatchingModel':
        """Load model from disk."""
        try:
            with open(path, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Model loaded from {path}")
            return model
        except FileNotFoundError:
            logger.warning(f"Model file not found: {path}, creating new model")
            return MatchingModel()


# Global instance
matching_model = None


def get_matching_model() -> MatchingModel:
    """Get or create matching model instance."""
    global matching_model
    if matching_model is None:
        # Try to load pre-trained model
        model_path = Path(settings.matching_model_path)
        if model_path.exists():
            matching_model = MatchingModel.load_model(model_path)
        else:
            matching_model = MatchingModel()
    return matching_model