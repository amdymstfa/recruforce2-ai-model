"""
Prediction Model - ML model to predict hiring success probability.
Uses Random Forest Classifier trained on historical data.
"""

import numpy as np
from typing import Dict
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle
from pathlib import Path
from src.core.config import settings
from src.utils.logger import get_logger

logger = get_logger()


class PredictionModel:
    """ML model for predicting hiring success probability."""
    
    def __init__(self):
        """Initialize prediction model."""
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        logger.info("Prediction model initialized")
    
    def extract_features(self, candidate_data: Dict, job_offer_data: Dict, 
                        matching_score: int) -> np.ndarray:
        """
        Extract features for ML prediction.
        
        Args:
            candidate_data: Candidate information
            job_offer_data: Job offer information
            matching_score: Pre-calculated matching score (0-100)
            
        Returns:
            Feature vector as numpy array
        """
        features = [
            matching_score,  
            candidate_data.get('total_experience_years', 0),
            len(candidate_data.get('skills', [])),
            len(candidate_data.get('languages', [])),
            len(candidate_data.get('educations', [])),
            job_offer_data.get('min_experience', 0),
            job_offer_data.get('max_experience', 20),
            len(job_offer_data.get('required_skills', []))
        ]
        
        return np.array(features).reshape(1, -1)
    
    def train(self, X: np.ndarray, y: np.ndarray):
        """
        Train the prediction model.
        
        Args:
            X: Feature matrix
            y: Target labels (0 or 1)
        """
        logger.info(f"Training model with {len(X)} samples")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # Calculate training accuracy
        accuracy = self.model.score(X_scaled, y)
        logger.info(f"Model trained - Accuracy: {accuracy:.2%}")
    
    def predict_success(self, candidate_data: Dict, job_offer_data: Dict, 
                       matching_score: int) -> Dict:
        """
        Predict hiring success probability.
        
        Args:
            candidate_data: Candidate information
            job_offer_data: Job offer requirements
            matching_score: Pre-calculated matching score
            
        Returns:
            Prediction result with probability and confidence
        """
        # Extract features
        features = self.extract_features(candidate_data, job_offer_data, matching_score)
        
        # If model is not trained, use rule-based prediction
        if not self.is_trained:
            return self._rule_based_prediction(matching_score)
        
        try:
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Predict probability
            proba = self.model.predict_proba(features_scaled)
            if proba.shape[1] < 2:
                return self._rule_based_prediction(matching_score)
            success_probability = proba[0][1]
            confidence = proba.max()
        except Exception:
            return self._rule_based_prediction(matching_score)
        
        # Generate explanation
        main_factors = self._generate_factors(
            matching_score, 
            candidate_data.get('total_experience_years', 0),
            len(candidate_data.get('skills', []))
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(success_probability, matching_score)
        
        result = {
            'matching_score': matching_score / 100.0,  # Normalize to 0-1
            'success_probability': round(success_probability, 3),
            'confidence': round(confidence, 3),
            'main_factors': main_factors,
            'recommendation': recommendation,
            'model_version': '1.0.0'
        }
        
        logger.info(f"Prediction: {success_probability:.2%} success probability")
        return result
    
    def _rule_based_prediction(self, matching_score: int) -> Dict:
        """
        Fallback rule-based prediction when ML model is not trained.
        
        Args:
            matching_score: Matching score (0-100)
            
        Returns:
            Prediction result
        """
        # Simple rule-based logic
        if matching_score >= 80:
            success_prob = 0.85
            recommendation = "STRONGLY_RECOMMENDED"
        elif matching_score >= 70:
            success_prob = 0.70
            recommendation = "RECOMMENDED"
        elif matching_score >= 60:
            success_prob = 0.55
            recommendation = "NEUTRAL"
        else:
            success_prob = 0.30
            recommendation = "NOT_RECOMMENDED"
        
        return {
            'matching_score': matching_score / 100.0,
            'success_probability': success_prob,
            'confidence': 0.75,
            'main_factors': f"Matching score: {matching_score}/100",
            'recommendation': recommendation,
            'model_version': '1.0.0-rule-based'
        }
    
    def _generate_factors(self, matching_score: int, experience_years: int, 
                         skills_count: int) -> str:
        """Generate explanation of main factors."""
        factors = []
        
        if matching_score >= 80:
            factors.append("Excellent skill alignment")
        elif matching_score >= 60:
            factors.append("Good skill match")
        else:
            factors.append("Limited skill overlap")
        
        if experience_years >= 5:
            factors.append("Strong experience")
        elif experience_years >= 2:
            factors.append("Adequate experience")
        
        if skills_count >= 10:
            factors.append("Diverse skill set")
        
        return ", ".join(factors) if factors else "Standard profile"
    
    def _generate_recommendation(self, success_probability: float, 
                                matching_score: int) -> str:
        """Generate hiring recommendation."""
        if success_probability >= 0.8 and matching_score >= 75:
            return "STRONGLY_RECOMMENDED"
        elif success_probability >= 0.6 and matching_score >= 60:
            return "RECOMMENDED"
        elif success_probability >= 0.4:
            return "NEUTRAL"
        else:
            return "NOT_RECOMMENDED"
    
    def save_model(self, path: Path):
        """Save model to disk."""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        logger.info(f"Model saved to {path}")
    
    @staticmethod
    def load_model(path: Path) -> 'PredictionModel':
        """Load model from disk."""
        try:
            with open(path, 'rb') as f:
                model_data = pickle.load(f)
            
            prediction_model = PredictionModel()
            prediction_model.model = model_data['model']
            prediction_model.scaler = model_data['scaler']
            prediction_model.is_trained = model_data['is_trained']
            
            logger.info(f"Model loaded from {path}")
            return prediction_model
        except FileNotFoundError:
            logger.warning(f"Model file not found: {path}, creating new model")
            return PredictionModel()


# Global instance
prediction_model = None


def get_prediction_model() -> PredictionModel:
    """Get or create prediction model instance."""
    global prediction_model
    if prediction_model is None:
        # Chemin vers le fichier défini dans settings
        model_path = Path(settings.models_dir) / "prediction_model.pkl"
        if model_path.exists():
            prediction_model = PredictionModel.load_model(model_path)
        else:
            prediction_model = PredictionModel()
    return prediction_model