FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Installation des libs Python
RUN pip install --no-cache-dir -r requirements.txt

# --- AJOUT ICI ---
# On installe le modèle pendant le build avec l'utilisateur root
RUN pip install https://github.com/explosion/spacy-models/releases/download/fr_core_news_md-3.7.0/fr_core_news_md-3.7.0.tar.gz
# -----------------

COPY . .

# Gestion des permissions
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# On simplifie le CMD car le modèle est déjà là
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]