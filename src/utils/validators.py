"""
Data validation utilities for AI service.
Validates input data for CV parsing, matching, and predictions.
"""

import re
from typing import List, Optional
from pydantic import BaseModel, validator, EmailStr


class EmailValidator:
    """Email validation utilities."""
    
    @staticmethod
    def is_valid(email: str) -> bool:
        """Check if email is valid."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


class PhoneValidator:
    """Phone number validation utilities."""
    
    @staticmethod
    def is_valid(phone: str) -> bool:
        """Check if phone number is valid (French format)."""
        # Remove spaces, dashes, dots
        cleaned = re.sub(r'[\s\-\.]', '', phone)
        # French phone: 10 digits starting with 0, or +33 followed by 9 digits
        pattern = r'^(0[1-9]\d{8}|(\+33|0033)[1-9]\d{8})$'
        return bool(re.match(pattern, cleaned))
    
    @staticmethod
    def normalize(phone: str) -> str:
        """Normalize phone number to standard format."""
        cleaned = re.sub(r'[\s\-\.]', '', phone)
        if cleaned.startswith('+33'):
            return f"0{cleaned[3:]}"
        elif cleaned.startswith('0033'):
            return f"0{cleaned[4:]}"
        return cleaned


class SkillValidator:
    """Skills validation utilities."""
    
    @staticmethod
    def normalize_skill_name(skill: str) -> str:
        """Normalize skill name (lowercase, trimmed)."""
        return skill.strip().lower()
    
    @staticmethod
    def is_valid_skill_level(level: str) -> bool:
        """Check if skill level is valid."""
        valid_levels = ['beginner', 'intermediate', 'advanced', 'expert']
        return level.lower() in valid_levels


class LanguageValidator:
    """Language proficiency validation."""
    
    @staticmethod
    def is_valid_level(level: str) -> bool:
        """Check if language level is valid (CEFR)."""
        valid_levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'native']
        return level.lower() in valid_levels


class ScoreValidator:
    """Score validation utilities."""
    
    @staticmethod
    def is_valid_matching_score(score: int) -> bool:
        """Check if matching score is valid (0-100)."""
        return 0 <= score <= 100
    
    @staticmethod
    def is_valid_probability(prob: float) -> bool:
        """Check if probability is valid (0.0-1.0)."""
        return 0.0 <= prob <= 1.0


def validate_candidate_data(data: dict) -> dict:
    """
    Validate candidate data from parsed CV.
    
    Args:
        data: Parsed candidate data
        
    Returns:
        Validated and normalized data
        
    Raises:
        ValueError: If validation fails
    """
    errors = []
    
    # Validate email
    if 'email' in data and data['email']:
        if not EmailValidator.is_valid(data['email']):
            errors.append(f"Invalid email: {data['email']}")
    
    # Validate phone
    if 'phone' in data and data['phone']:
        if not PhoneValidator.is_valid(data['phone']):
            errors.append(f"Invalid phone: {data['phone']}")
        else:
            data['phone'] = PhoneValidator.normalize(data['phone'])
    
    # Validate skills
    if 'skills' in data:
        validated_skills = []
        for skill in data['skills']:
            if isinstance(skill, dict):
                skill['name'] = SkillValidator.normalize_skill_name(skill.get('name', ''))
                validated_skills.append(skill)
        data['skills'] = validated_skills
    
    if errors:
        raise ValueError(f"Validation errors: {', '.join(errors)}")
    
    return data


def validate_matching_input(candidate_id: int, job_offer_id: int) -> bool:
    """
    Validate matching request input.
    
    Args:
        candidate_id: Candidate ID
        job_offer_id: Job offer ID
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If validation fails
    """
    if candidate_id <= 0:
        raise ValueError("Invalid candidate ID")
    if job_offer_id <= 0:
        raise ValueError("Invalid job offer ID")
    return True