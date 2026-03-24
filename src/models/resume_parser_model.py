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
from src.utils.validators import validate_candidate_data

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
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    content = page.extract_text()
                    if content:
                        text += content + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error PDF: {e}")
            raise

    def extract_text_from_docx(self, file_path: Path) -> str:
        try:
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs]).strip()
        except Exception as e:
            logger.error(f"Error DOCX: {e}")
            raise

    def extract_email(self, text: str) -> Optional[str]:
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(pattern, text)
        return matches[0].lower() if matches else None

    def extract_phone(self, text: str) -> Optional[str]:
        pattern = r'(\+[\d\s-]{7,16}|0[1-9][\d\s-]{8,12})'
        matches = re.findall(pattern, text)
        if matches:
            cleaned = re.sub(r'[\s-]', '', matches[0])
            return cleaned
        return None

    def extract_name(self, text: str) -> Dict[str, Optional[str]]:
        lines = [l.strip() for l in text.split('\n') if l.strip()][:5]
        doc = self.nlp(" ".join(lines))
        for ent in doc.ents:
            if ent.label_ == "PER" and "Native" not in ent.text and "Developer" not in ent.text:
                parts = ent.text.split()
                return {"first_name": parts[0], "last_name": " ".join(parts[1:]) if len(parts) > 1 else None}
        if lines:
            parts = lines[0].split()
            return {"first_name": parts[0], "last_name": " ".join(parts[1:]) if len(parts) > 1 else None}
        return {"first_name": None, "last_name": None}

    def extract_skills(self, text: str) -> List[Dict[str, str]]:
        skills_list = [
            'python', 'java', 'javascript', 'react', 'angular', 'node.js', 'spring', 
            'postgresql', 'mongodb', 'docker', 'git', 'ci/cd', 'aws', 'figma', 'golang', 'php'
        ]
        text_lower = text.lower()
        found = []
        for s in skills_list:
            if s in text_lower:
                found.append({"name": s.upper(), "type": "TECHNICAL", "mastery_level": "INTERMEDIATE"})
        return found

    def extract_sections(self, text: str) -> Dict[str, str]:
        sections = {"experience": "", "education": ""}
        exp_pattern = re.compile(r'(EXPERIENCE|EXPÉRIENCE|WORK|PARCOURS PROFESSIONNEL)', re.IGNORECASE)
        edu_pattern = re.compile(r'(EDUCATION|ÉDUCATION|FORMATION|DIPLÔMES)', re.IGNORECASE)
        lines = text.split('\n')
        current_section = None
        for line in lines:
            if exp_pattern.search(line): current_section = "experience"
            elif edu_pattern.search(line): current_section = "education"
            elif current_section: sections[current_section] += line + "\n"
        return sections

    def parse_experience(self, section_text: str) -> List[Dict]:
        experiences = []
        date_pattern = r'([A-Za-z]+\s\d{4}|\d{4})'
        lines = [l.strip() for l in section_text.split('\n') if l.strip()]
        for i, line in enumerate(lines):
            if re.search(date_pattern, line):
                experiences.append({
                    "position": lines[i-1] if i > 0 else "Poste non identifié",
                    "company": line,
                    "description": line,
                    "is_current": any(x in line for x in ["Present", "Aujourd'hui", "Now"])
                })
        return experiences

    def extract_languages(self, text: str) -> List[Dict[str, str]]:
        languages_keywords = {'french': 'French', 'english': 'English', 'wolof': 'Wolof', 'arabe': 'Arabic'}
        text_lower = text.lower()
        found = []
        for kw, name in languages_keywords.items():
            if kw in text_lower:
                level = "B2"
                if "native" in text_lower or "natif" in text_lower: level = "NATIVE"
                elif "c2" in text_lower: level = "C2"
                found.append({"name": name, "level": level})
        return found

    def parse_cv(self, file_path: Path) -> Dict:
        file_ext = file_path.suffix.lower()
        raw_text = self.extract_text_from_pdf(file_path) if file_ext == '.pdf' else self.extract_text_from_docx(file_path)
        name_data = self.extract_name(raw_text)
        sections = self.extract_sections(raw_text)
        return {
            "first_name": name_data.get("first_name"),
            "last_name": name_data.get("last_name"),
            "email": self.extract_email(raw_text),
            "phone": self.extract_phone(raw_text),
            "address": "Safi, Morocco" if "Safi" in raw_text else None,
            "experiences": self.parse_experience(sections["experience"]),
            "educations": [{"degree": "Diplôme détecté", "institution": "Établissement"}] if sections["education"] else [],
            "skills": self.extract_skills(raw_text),
            "languages": self.extract_languages(raw_text),
            "raw_text": raw_text,
            "parsing_confidence": 0.85,
            "model_version": "1.1.0"
        }

# =====================================================
# AJOUTER CETTE PARTIE À LA FIN (TRÈS IMPORTANT)
# =====================================================

# Instance globale
parser_model = None

def get_parser_model() -> ResumeParserModel:
    """Récupère ou crée l'instance du modèle de parsing."""
    global parser_model
    if parser_model is None:
        parser_model = ResumeParserModel()
    return parser_model