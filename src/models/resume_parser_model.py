"""
Resume Parser Model using NLP (spaCy).
Extracts structured data from PDF and DOCX CVs.
"""

import re
import spacy
from typing import Dict, List, Optional
from pathlib import Path
import PyPDF2
from docx import Document
from src.core.config import settings
from src.utils.logger import get_logger
from src.utils.validators import EmailValidator, PhoneValidator

logger = get_logger()


class ResumeParserModel:
    """NLP model for parsing resumes and extracting structured data."""
    
    def __init__(self):
        """Initialize spaCy NLP model."""
        try:
            self.nlp = spacy.load(settings.spacy_model)
            logger.info(f"spaCy model loaded: {settings.spacy_model}")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            raise
    
    def extract_text_from_pdf(self, file_path: Path) -> str:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            logger.info(f"Extracted {len(text)} characters from PDF")
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise
    
    def extract_text_from_docx(self, file_path: Path) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        try:
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            logger.info(f"Extracted {len(text)} characters from DOCX")
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            raise
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(pattern, text)
        for email in matches:
            if EmailValidator.is_valid(email):
                return email.lower()
        return None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text."""
        # French phone patterns
        patterns = [
            r'\b0[1-9](?:\s?\d{2}){4}\b',  # 01 23 45 67 89
            r'\b\+33\s?[1-9](?:\s?\d{2}){4}\b',  # +33 1 23 45 67 89
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for phone in matches:
                cleaned = re.sub(r'\s', '', phone)
                if PhoneValidator.is_valid(cleaned):
                    return PhoneValidator.normalize(cleaned)
        return None
    
    def extract_name(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract first and last name from text.
        Uses NER (Named Entity Recognition).
        """
        doc = self.nlp(text[:500])  # Analyze first 500 chars
        
        names = []
        for ent in doc.ents:
            if ent.label_ == "PER":  # Person entity
                names.append(ent.text)
        
        if names:
            # Assume first name is the first detected person
            full_name = names[0].split()
            return {
                "first_name": full_name[0] if len(full_name) > 0 else None,
                "last_name": " ".join(full_name[1:]) if len(full_name) > 1 else None
            }
        return {"first_name": None, "last_name": None}
    
    def extract_skills(self, text: str) -> List[Dict[str, str]]:
        """
        Extract skills from text using keyword matching.
        """
        # Common technical skills (extend this list)
        technical_skills = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue',
            'spring', 'django', 'flask', 'fastapi', 'node.js', 'express',
            'postgresql', 'mongodb', 'mysql', 'redis', 'docker', 'kubernetes',
            'aws', 'azure', 'gcp', 'git', 'ci/cd', 'agile', 'scrum'
        ]
        
        # Common soft skills
        soft_skills = [
            'communication', 'leadership', 'teamwork', 'problem solving',
            'critical thinking', 'adaptability', 'creativity', 'time management'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        # Technical skills
        for skill in technical_skills:
            if skill in text_lower:
                found_skills.append({
                    "name": skill.title(),
                    "type": "TECHNICAL",
                    "mastery_level": "INTERMEDIATE"  # Default level
                })
        
        # Soft skills
        for skill in soft_skills:
            if skill in text_lower:
                found_skills.append({
                    "name": skill.title(),
                    "type": "SOFT",
                    "mastery_level": "INTERMEDIATE"
                })
        
        return found_skills
    
    def extract_languages(self, text: str) -> List[Dict[str, str]]:
        """Extract languages from text."""
        languages_keywords = {
            'français': 'French',
            'french': 'French',
            'anglais': 'English',
            'english': 'English',
            'espagnol': 'Spanish',
            'spanish': 'Spanish',
            'arabe': 'Arabic',
            'arabic': 'Arabic',
            'allemand': 'German',
            'german': 'German'
        }
        
        text_lower = text.lower()
        found_languages = []
        
        for keyword, lang_name in languages_keywords.items():
            if keyword in text_lower:
                # Try to find level near the language mention
                level = "B2"  # Default level
                if any(lvl in text_lower for lvl in ['natif', 'native', 'maternelle']):
                    level = "NATIVE"
                elif any(lvl in text_lower for lvl in ['courant', 'fluent', 'c1', 'c2']):
                    level = "C1"
                
                found_languages.append({
                    "name": lang_name,
                    "level": level
                })
        
        return found_languages
    
    def parse_cv(self, file_path: Path) -> Dict:
        """
        Main parsing method - extracts all information from CV.
        
        Args:
            file_path: Path to CV file (PDF or DOCX)
            
        Returns:
            Structured CV data
        """
        logger.info(f"Parsing CV: {file_path}")
        
        # Extract text based on file type
        file_ext = file_path.suffix.lower()
        if file_ext == '.pdf':
            raw_text = self.extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            raw_text = self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Extract structured data
        name_data = self.extract_name(raw_text)
        
        parsed_data = {
            "first_name": name_data.get("first_name"),
            "last_name": name_data.get("last_name"),
            "email": self.extract_email(raw_text),
            "phone": self.extract_phone(raw_text),
            "address": None,  # TODO: Implement address extraction
            
            "experiences": [],  # TODO: Implement experience extraction
            "educations": [],   # TODO: Implement education extraction
            "skills": self.extract_skills(raw_text),
            "languages": self.extract_languages(raw_text),
            
            "raw_text": raw_text[:1000],  # First 1000 chars for reference
            "parsing_confidence": 0.75,  # Placeholder confidence score
            "model_version": "1.0.0"
        }
        
        logger.info(f"CV parsed successfully - Found {len(parsed_data['skills'])} skills")
        return parsed_data


# Global instance
parser_model = None


def get_parser_model() -> ResumeParserModel:
    """Get or create parser model instance."""
    global parser_model
    if parser_model is None:
        parser_model = ResumeParserModel()
    return parser_model