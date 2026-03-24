"""
Data validation utilities for AI service.
Validates input data for CV parsing, matching, and predictions.
"""

import re
from typing import List, Optional

class EmailValidator:
    """Email validation utilities."""
    
    @staticmethod
    def is_valid(email: str) -> bool:
        """Check if email is valid."""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


class PhoneValidator:
    """Phone number validation utilities updated for International support."""
    
    @staticmethod
    def is_valid(phone: str) -> bool:
        """
        Check if phone number is valid.
        Supports International formats (+XXX) and local formats.
        """
        if not phone:
            return False
        # Supprime les espaces, tirets, parenthèses et points pour la validation
        cleaned = re.sub(r'[\s\-\.\(\)]', '', phone)
        
        # Regex plus souple : 
        # Commence par + ou 00 suivi de 7 à 15 chiffres
        # OU commence par 0 suivi de 9 chiffres (format local)
        pattern = r'^(\+|00)?[1-9]\d{6,14}$|^0[1-9]\d{8}$'
        return bool(re.match(pattern, cleaned))
    
    @staticmethod
    def normalize(phone: str) -> str:
        """Normalize phone number to a clean string of digits with leading + if present."""
        if not phone:
            return ""
        
        # Conserver le '+' s'il est au début
        has_plus = phone.strip().startswith('+')
        
        # Extraire uniquement les chiffres
        digits = "".join(re.findall(r'\d+', phone))
        
        # Gérer le cas du 00 au début (le transformer en +)
        if phone.strip().startswith('00'):
            return f"+{digits[2:]}"
            
        return f"+{digits}" if has_plus else digits


class SkillValidator:
    """Skills validation utilities."""
    
    @staticmethod
    def normalize_skill_name(skill: str) -> str:
        """Normalize skill name (lowercase, trimmed)."""
        if not skill:
            return ""
        return skill.strip().lower()
    
    @staticmethod
    def is_valid_skill_level(level: str) -> bool:
        """Check if skill level is valid."""
        if not level:
            return False
        valid_levels = ['beginner', 'intermediate', 'advanced', 'expert']
        return level.lower() in valid_levels


class LanguageValidator:
    """Language proficiency validation."""
    
    @staticmethod
    def is_valid_level(level: str) -> bool:
        """Check if language level is valid (CEFR)."""
        if not level:
            return False
        valid_levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'native']
        return level.lower() in valid_levels


class ScoreValidator:
    """Score validation utilities."""
    
    @staticmethod
    def is_valid_matching_score(score: int) -> bool:
        """Check if matching score is valid (0-100)."""
        try:
            return 0 <= int(score) <= 100
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_probability(prob: float) -> bool:
        """Check if probability is valid (0.0-1.0)."""
        try:
            return 0.0 <= float(prob) <= 1.0
        except (ValueError, TypeError):
            return False


def validate_candidate_data(data: dict) -> dict:
    """
    Validate candidate data from parsed CV.
    """
    errors = []
    
    # Validate email
    email = data.get('email')
    if email:
        if not EmailValidator.is_valid(email):
            errors.append(f"Invalid email format: {email}")
    
    # Validate phone
    phone = data.get('phone')
    if phone:
        if not PhoneValidator.is_valid(phone):
            errors.append(f"Invalid phone: {phone}")
        else:
            data['phone'] = PhoneValidator.normalize(phone)
    
    # Validate skills
    if 'skills' in data and data['skills']:
        validated_skills = []
        for skill in data['skills']:
            if isinstance(skill, dict):
                name = skill.get('name', '')
                if name:
                    skill['name'] = SkillValidator.normalize_skill_name(name)
                    validated_skills.append(skill)
        data['skills'] = validated_skills
    
    if errors:
        # On log les erreurs pour le debug mais on peut choisir d'être moins fataliste
        # Ici on garde le raise ValueError pour correspondre à ton architecture actuelle
        raise ValueError(f"Validation errors: {', '.join(errors)}")
    
    return data


def validate_matching_input(candidate_id: int, job_offer_id: int) -> bool:
    """
    Validate matching request input.
    """
    if not candidate_id or int(candidate_id) <= 0:
        raise ValueError("Invalid candidate ID")
    if not job_offer_id or int(job_offer_id) <= 0:
        raise ValueError("Invalid job offer ID")
    return True