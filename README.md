# RecruForce2 AI Microservice 🤖

Intelligent AI service for CV parsing, candidate-job matching, and hiring success predictions.

## 🎯 Features

- **CV Parsing**: Extract structured data from PDF and DOCX resumes using NLP
- **Matching Algorithm**: Calculate compatibility scores between candidates and job offers
- **ML Predictions**: Predict hiring success probability using Random Forest
- **MongoDB Integration**: Store AI logs and parsed CV data
- **REST API**: FastAPI with automatic Swagger documentation

---

## 🏗️ Architecture

```
recruforce2-ai-model/
├── src/
│   ├── api/              # FastAPI endpoints
│   ├── core/             # Configuration
│   ├── models/           # ML models (parsing, matching, prediction)
│   ├── services/         # Business logic
│   └── utils/            # Utilities (logger, validators, file handler)
├── tests/                # Unit and integration tests
├── data/                 # Sample CVs and NLP models
├── persistence/          # Trained ML models
├── logs/                 # Application logs
└── uploads/              # Temporary CV uploads
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB 6.0+
- 2GB RAM minimum

### Option 1: Local Development

```bash
# 1. Clone the repository
git clone <repo-url>
cd recruforce2-ai-model

# 2. Copy environment file
cp .env.example .env
# Edit .env with your settings

# 3. Run startup script
chmod +x run.sh
./run.sh
```

The API will be available at http://localhost:8000

### Option 2: Docker

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start services
docker-compose up -d

# 3. Check logs
docker-compose logs -f ai-service
```

---

## 📚 API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Endpoints

#### 1. Parse CV
```bash
POST /api/parse-cv
Content-Type: multipart/form-data

# Example with curl
curl -X POST "http://localhost:8000/api/parse-cv?candidate_id=1" \
  -F "file=@cv.pdf"
```

**Response:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "0612345678",
  "skills": [
    {"name": "Python", "type": "TECHNICAL", "mastery_level": "ADVANCED"}
  ],
  "languages": [
    {"name": "French", "level": "NATIVE"}
  ],
  "parsing_confidence": 0.85,
  "parsed_cv_id": "507f1f77bcf86cd799439011"
}
```

#### 2. Calculate Matching Score
```bash
POST /api/match-score
Content-Type: application/json

{
  "candidate_id": 1,
  "job_offer_id": 5
}
```

**Response:**
```json
{
  "candidate_id": 1,
  "job_offer_id": 5,
  "matching_score": 75,
  "is_qualified": true,
  "matched_skills": ["python", "react", "docker"],
  "missing_skills": ["kubernetes"],
  "confidence": 0.85
}
```

#### 3. Predict Hiring Success
```bash
POST /api/predict
Content-Type: application/json

{
  "candidate_id": 1,
  "job_offer_id": 5
}
```

**Response:**
```json
{
  "candidate_id": 1,
  "job_offer_id": 5,
  "matching_score": 0.75,
  "success_probability": 0.82,
  "confidence": 0.88,
  "main_factors": "Excellent skill alignment, Strong experience",
  "recommendation": "STRONGLY_RECOMMENDED"
}
```

---

## 🔧 Configuration

Edit `.env` file:

```bash
# Application
DEBUG=True
HOST=0.0.0.0
PORT=8000

# MongoDB
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=recruforce2_dev

# Backend API
BACKEND_API_URL=http://localhost:8080

# Thresholds
MATCHING_THRESHOLD=60
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_cv_parser.py -v
```

---

## 📊 MongoDB Collections

### `parsed_cvs`
Stores structured CV data extracted by NLP.

### `ai_logs`
Logs all AI operations (parsing, matching, predictions) with timestamps, payloads, and performance metrics.

---

## 🔗 Integration with Backend

The AI service communicates with the Spring Boot backend:

```
Backend (Spring Boot) → HTTP POST → AI Service (FastAPI)
                      ← JSON Response ←
```

Backend calls:
- `POST /api/parse-cv` when CV is uploaded
- `POST /api/match-score` when application is submitted
- `POST /api/predict` for hiring recommendations

---

## 🛠️ Development

### Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

### Run in Development Mode
```bash
uvicorn src.main:app --reload --port 8000
```

### Code Quality
```bash
# Format code
black src/

# Lint
flake8 src/

# Sort imports
isort src/
```

---

## 📦 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in .env
- [ ] Configure proper CORS origins
- [ ] Set strong MongoDB credentials
- [ ] Configure SSL/TLS
- [ ] Set up monitoring and alerts
- [ ] Configure backup for MongoDB
- [ ] Set appropriate resource limits

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🐛 Troubleshooting

### MongoDB Connection Failed
```bash
# Check MongoDB is running
docker-compose ps

# Check logs
docker-compose logs mongodb
```

### spaCy Model Not Found
```bash
# Download French model
python -m spacy download fr_core_news_md
```

### File Upload Errors
```bash
# Check upload directory permissions
chmod 777 uploads/
```

---

## 📈 Performance

- **CV Parsing**: ~2-5 seconds per CV
- **Matching Calculation**: ~100ms
- **ML Prediction**: ~50ms
- **Concurrent Requests**: Supports 50+ concurrent users

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

---

## 📄 License

Proprietary - RecruForce2 © 2024

---

## 📞 Support

- **Documentation**: http://localhost:8000/docs
- **Logs**: `tail -f logs/ai_service.log`
- **Health**: http://localhost:8000/health

---

**Built with ❤️ for RecruForce2**