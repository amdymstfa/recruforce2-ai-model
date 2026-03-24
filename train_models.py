from pathlib import Path
import numpy as np
from src.models.prediction_model import PredictionModel
from src.models.matching_model import MatchingModel

# Créer le dossier si pas existant
Path('persistence/trained_models').mkdir(parents=True, exist_ok=True)

# Exemple de données synthétiques pour entraîner le modèle de prédiction
X = np.array([
    [85,5,10,2,2,3,8,8],
    [70,3,7,1,1,2,6,6]
])
y = np.array([1,1])

# Entraîner et sauvegarder le modèle de prédiction
pm = PredictionModel()
pm.train(X,y)
pm.save_model(Path('persistence/trained_models/prediction_model.pkl'))

# Sauvegarder le modèle de matching
mm = MatchingModel()
mm.save_model(Path('persistence/trained_models/matching_score_v1.pkl'))

print("Models saved!")