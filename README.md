# LandSight AI

> AI-Powered Predictive Analytics Platform for Early Detection of Land Acquisition Delays.

---

## 1. Project Overview
**LandSight AI** is a decision-support intelligence platform built to monitor, predict, and mitigate delays in infrastructure land acquisition workflows. By combining geospatial GIS mapping with predictive machine learning (survival analysis and gradient boosting) and explainable AI (SHAP), LandSight AI flags potential land acquisition bottlenecks months before critical deadlines are breached.

---

## 2. Problem Statement (SIH26017)
- **ID**: SIH26017
- **Title**: AI-powered predictive analytics platform for early detection of land acquisition delays.
- **Background**: Infrastructure and capital projects frequently face significant cost and time overruns resulting from land acquisition hurdles—including complex statutory milestone transitions, title disputes, valuation conflicts, and rehabilitation & resettlement (R&R) issues.
- **Solution**: LandSight AI provides predictive intelligence, early risk scoring, spatial visualization, and root-cause explainability for administrative decision-makers to proactively intervene and safeguard project timelines.

---

## 3. Tech Stack

- **Machine Learning & Analytics**:
  - Python (Scikit-Learn, XGBoost / LightGBM)
  - Survival Analysis (Lifelines / Cox Proportional Hazards)
  - Explainable AI (SHAP)
- **Backend API**:
  - FastAPI
  - SQLAlchemy / GeoAlchemy2
  - PostgreSQL with PostGIS extension
- **Frontend Dashboard**:
  - React 18+ (Vite)
  - Geospatial mapping (Mapbox GL / Leaflet)
  - Charting & Visual Analytics
- **DevOps & Infrastructure**:
  - Docker & Docker Compose

---

## 4. Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Git
- Docker & Docker Compose (optional, for PostGIS)

### 1. Clone & Environment Setup
```bash
# Clone the repository
git clone <repository-url>
cd landsight-ai

# Activate root Python virtual environment
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Backend Setup
```bash
# Install backend dependencies (when ready)
pip install -r backend/requirements.txt

# Run backend service
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
# Navigate to frontend and install dependencies
cd frontend
npm install

# Start Vite development server
npm run dev
```

### 4. Database Services (Optional)
```bash
# Spin up PostgreSQL + PostGIS container
docker-compose up -d
```

---

## 5. Project Structure

```
.
├── data/                   # Raw & synthetic datasets, data dictionary
│   └── DATA_ASSUMPTIONS.md
├── ml/                     # Feature engineering, models, SHAP, survival analysis
│   ├── models/
│   └── notebooks/
├── backend/                # FastAPI service
│   ├── app/
│   │   ├── routers/
│   │   ├── models/         # DB schema (SQLAlchemy)
│   │   └── services/
│   └── requirements.txt
├── frontend/               # React dashboard (Vite)
├── docs/                   # Architecture notes, API docs, demo script
├── .gitignore              # Python, Node, .env, venv, cache, node_modules
├── README.md               # Project documentation
└── docker-compose.yml      # PostGIS database service
```

---

## 6. Team (Team Genesis)
Developed with passion by **Team Genesis** for Smart India Hackathon (SIH).
