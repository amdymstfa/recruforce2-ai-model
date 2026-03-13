#!/bin/bash

# ===================================================
# RecruForce2 AI Service - Startup Script
# ===================================================

set -e

echo "🚀 Starting RecruForce2 AI Service..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ .env created. Please configure it before running again."
    exit 1
fi

# Create necessary directories
mkdir -p logs uploads persistence/trained_models

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo "📦 Downloading spaCy model..."
    python -m spacy download fr_core_news_md
fi

# Run the application
echo "🎯 Starting FastAPI server..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload