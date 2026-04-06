# 🌾 Kishaan Deepak — Crop Intelligence Platform

An AI-powered Flask web application for Indian farmers featuring:

- **Crop Yield Prediction** — Linear Regression pipeline on agronomic inputs
- **Paddy Disease Detection** — HOG features + Logistic Regression on leaf images
- **AI Chatbot** — Groq-powered agricultural assistant (streaming)

---

## 📁 Project Structure

```
kishaan_deepak/
├── app/
│   ├── __init__.py              # Application factory (create_app)
│   ├── logger.py                # Shared logging setup
│   ├── models_loader/
│   │   ├── __init__.py
│   │   └── loader.py            # Singleton model store
│   ├── routes/
│   │   ├── yield_routes.py      # GET /api/yield/options  POST /api/yield/predict
│   │   ├── disease_routes.py    # GET /api/disease/classes  POST /api/disease/predict
│   │   ├── chat_routes.py       # POST /api/chat
│   │   └── health_routes.py     # GET /api/health
│   ├── services/
│   │   ├── yield_service.py     # Yield business logic
│   │   ├── disease_service.py   # Disease detection business logic
│   │   └── chat_service.py      # Groq streaming wrapper
│   └── utils/
│       ├── validators.py        # Input validation helpers
│       └── image_utils.py       # Safe image I/O + HOG extraction
├── models/
│   ├── crop_yield_model.joblib
│   └── paddy_disease_model.pkl
├── static/
│   ├── css/style.css
│   └── js/
│       ├── main.js
│       └── chatbot.js
├── templates/
│   └── index.html
├── data/
│   └── indian_crop_climate_data.csv
├── dataset/                     # Disease images for (re)training
├── logs/                        # Auto-created at runtime
├── uploads/                     # Temp uploads (auto-cleaned per request)
├── app.py                       # Entry point
├── config.py                    # All configuration constants
├── paddy-disease-classification.py   # Model training script
├── requirements.txt
├── .env                         # Real secrets — do NOT commit
└── .env.example                 # Template to share safely
```

---

## 🚀 Quick Start

### 1. Clone & set up environment

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set GROQ_API_KEY
```

### 3. (Optional) Train the disease model

```bash
# Put disease images in dataset/<ClassName>/
python paddy-disease-classification.py
```

### 4. Run the server

```bash
# Development
python app.py

# Production
gunicorn "app:flask_app" --workers 2 --bind 0.0.0.0:5000
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Model status |
| GET | `/api/yield/options` | Dropdown values for yield form |
| POST | `/api/yield/predict` | Predict crop yield (JSON body) |
| GET | `/api/disease/classes` | List disease classes |
| POST | `/api/disease/predict` | Detect disease from image upload |
| POST | `/api/chat` | Streaming AI chatbot |

### POST /api/yield/predict — example body

```json
{
  "crop_type":        "Rice",
  "region":           "South",
  "temperature_c":    28.5,
  "rainfall_mm":      1200,
  "humidity_percent": 75,
  "soil_type":        "Clay"
}
```

### POST /api/disease/predict — example

```bash
curl -X POST http://localhost:5000/api/disease/predict \
     -F "file=@leaf.jpg"
```

---

## ⚙️ Configuration (`config.py` / `.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `change-me` | Flask session secret |
| `FLASK_DEBUG` | `false` | Enable debug mode |
| `FLASK_PORT` | `5000` | Server port |
| `ALLOWED_ORIGINS` | `http://localhost:5000` | Comma-separated CORS origins |
| `GROQ_API_KEY` | — | Required for chatbot |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## 🏗️ Architecture Notes

- **Application factory** (`create_app`) keeps the app testable and prevents circular imports.
- **Models are loaded once** at startup via `model_store.load_all()`.
- **Blueprints** separate concerns: each feature area has its own route file.
- **Services** contain zero Flask code — they can be imported and tested without an app context.
- **Validators** are pure functions returning `(bool, message)` tuples.
- **Uploads** are assigned a UUID prefix, processed in memory, then deleted immediately.
- **Logs** rotate at 2 MB (up to 5 files) and are written to `logs/app.log`.
