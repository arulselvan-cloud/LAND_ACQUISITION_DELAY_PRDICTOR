# LandSight AI: AI-Powered Predictive Analytics Platform for Infrastructure Land Acquisition Delays

[![Smart India Hackathon](https://img.shields.io/badge/SIH-2024-orange.svg)](https://www.sih.gov.in/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18_%2B_Vite-61DAFB.svg)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_16_%2B_PostGIS-336791.svg)](https://www.postgresql.org/)
[![Gemini](https://img.shields.io/badge/LLM-Gemini_2.5_Flash-8E75B2.svg)](https://ai.google.dev/)
[![Tests](https://img.shields.io/badge/Tests-PyTest_Passing-brightgreen.svg)]()

> **Problem Statement ID**: SIH26017  
> **Theme**: Infrastructure & Capital Projects / Ministry of Statistics & Programme Implementation (MoSPI)  
> **Mandate**: Early detection, root-cause explainability, sequential delay propagation, and prescriptive AI mitigation for land acquisition bottlenecks under the RFCTLARR Act, 2013.

---

## 1. Executive Summary

Land acquisition hurdles account for over **60% of infrastructure project delays** and billions of dollars in capital overruns across Indian national highways, high-speed rail networks, industrial corridors, and energy pipelines. Under the **Right to Fair Compensation and Transparency in Land Acquisition, Rehabilitation and Resettlement Act, 2013 (RFCTLARR 2013)**, statutory milestones operate as a tightly coupled, sequential dependency chain. A single stay order or solatium dispute at an early milestone halts downstream possession and construction.

**LandSight AI** transforms reactive bureaucratic firefighting into proactive administrative governance through a closed-loop **5-Stage Statutory Pipeline**:
1. **Stage 1 (Land Data)**: Spatial PostGIS cadastral parcel ingestion, Section 11/19/21 statutory milestone tracking, PAF records, and compensation treasury disbursements.
2. **Stage 2 (AI Prediction)**: Calibrated multiclass risk classification (Low, Medium, High, Critical) and cumulative delay probability forecasting via XGBoost.
3. **Stage 3 (Explainability)**: Local SHAP (TreeExplainer) attribution isolating exact delay drivers (active stay orders, solatium gaps, stakeholder responsiveness) with magnitude and direction.
4. **Stage 4 (Impact Map)**: Autoregressive milestone delay propagation cascade quantifying upstream-to-downstream bottleneck transmission across all 5 statutory stages.
5. **Stage 5 (Intervention & Simulation)**: Interactive counterfactual "What-If" engine estimating delay days saved, coupled with **Gemini 2.5 Flash** generating authoritative 3-sentence administrative action memos for District Collectors and SLAOs.

---

## 2. System Architecture

```
                                  LANDSIGHT AI PLATFORM
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   REACT 18 + VITE FRONTEND                               │
 │   ┌───────────────────────┐  ┌─────────────────────────┐  ┌───────────────────────────┐  │
 │   │  National Heatmap     │  │  Project Registry Table │  │  5-Stage Pipeline Detail  │  │
 │   │  (District GeoJSON)   │  │  (Sorting & Filters)    │  │  (SHAP, What-If, LLM Memo)│  │
 │   └───────────────────────┘  └─────────────────────────┘  └───────────────────────────┘  │
 └────────────────────────────────────────────┬────────────────────────────────────────────┘
                                              │ REST API (/api)
 ┌────────────────────────────────────────────▼────────────────────────────────────────────┐
 │                                     FASTAPI BACKEND SERVICE                             │
 │   ┌───────────────────────┐  ┌─────────────────────────┐  ┌───────────────────────────┐  │
 │   │  Predictions Router   │  │  Recommendations Engine │  │  Dashboard & Spatial API  │  │
 │   │  (/predict, /what-if) │  │  (Gemini 2.5 Flash LLM) │  │  (/summary, /districts)   │  │
 │   └───────────┬───────────┘  └────────────┬────────────┘  └─────────────┬─────────────┘  │
 └───────────────┼───────────────────────────┼─────────────────────────────┼────────────────┘
                 │                           │                             │
 ┌───────────────▼───────────┐ ┌─────────────▼─────────────┐ ┌─────────────▼────────────────┐
 │     ML MODEL ARTIFACTS    │ │    EXTERNAL SERVICES      │ │     PERSISTENCE & SPATIAL    │
 │ - XGBoost Risk Classifier │ │ - Google Gemini Flash API │ │ - PostgreSQL 16 + PostGIS    │
 │ - Cox PH Survival Models  │ │   (Action Memo Synthesis) │ │ - SQLAlchemy 2.0 ORM         │
 │ - OLS Propagation Cascade │ │ - Leaflet / GeoJSON Tiles │ │ - GeoAlchemy2 Geometry       │
 │ - SHAP TreeExplainer      │ │                           │ │ - Alembic Migrations         │
 └───────────────────────────┘ └───────────────────────────┘ └──────────────────────────────┘
```

---

## 3. Prerequisites

Ensure you have the following installed on your host system:
- **Docker & Docker Compose** (v20.10+ recommended)
- **Python 3.11+** (Python 3.11.x verified)
- **Node.js 18+** & `npm` (v18.x or v20.x LTS)
- **Git**

---

## 4. Quickstart Setup (Zero to Running in 5 Minutes)

### Step 1: Clone the Repository
```bash
git clone https://github.com/arulselvan-cloud/LANDSIGHT_AI.git
cd LANDSIGHT_AI
```

### Step 2: Configure Environment Variables
Copy `.env.example` to create your local `.env`:
```bash
cp .env.example .env
```

Open `.env` and set your configuration.
> **Getting a Gemini API Key**:
> 1. Visit [Google AI Studio](https://aistudio.google.com/).
> 2. Sign in with your Google account and click **"Get API key"**.
> 3. Create a free API key and paste it into `.env`:
>    ```env
>    GEMINI_API_KEY=your_gemini_api_key_here
>    GEMINI_TIMEOUT_SECONDS=12.0
>    ```
*(Note: If no key is configured or if the API times out, LandSight AI automatically falls back to deterministic rule-based administrative action templates without breaking).*

### Step 3: Start the Spatial Database (Docker)
Start PostgreSQL with the PostGIS extension using Docker Compose:
```bash
docker compose up -d
```
Verify the container is healthy:
```bash
docker compose ps
```

### Step 4: Setup Python Backend Environment
```bash
# 1. Create and activate a Python virtual environment
# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\activate

# 2. Install backend dependencies
pip install -r backend/requirements.txt
```

### Step 5: Run Database Migrations & Ingest Data
```bash
# 1. Apply Alembic schema migrations
alembic -c backend/alembic.ini upgrade head

# 2. Ingest 3,500 calibrated synthetic projects across 12 Indian states + 3 real showcase projects
python backend/scripts/generate_synthetic_dataset.py

# 3. Populate real showcase projects, statutory stages, and baseline alerts
python backend/scripts/seed_data.py
```

### Step 6: Start the FastAPI Backend
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- API Health Check: `http://localhost:8000/api/health`
- Interactive OpenAPI Swagger Docs: `http://localhost:8000/docs`

### Step 7: Start the React Frontend Dashboard
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open your browser and navigate to:
👉 **`http://localhost:5173`**

---

## 5. Automated Test Suite

Run the full integration test suite with `pytest`:
```bash
# From workspace root with venv active:
pytest backend/tests/ -v
```

The test suite validates:
- [x] **Showcase Project Inference**: `CBIC-TN-PKG02` (Critical), `MAHSR-MH-PAL03` (Critical), `BSRP-KA-CORR04` (Low).
- [x] **Error Handling (404 Not Found)**: Invalid project IDs across `/predict`, `/explain`, `/propagation`, `/what-if`.
- [x] **Input Validation (422 Unprocessable Entity)**: Out-of-range slider inputs, negative counts, empty bodies.
- [x] **SHAP Explainability Structure**: Exactly 5 top risk drivers with verified directions (`increases_risk`/`decreases_risk`).
- [x] **What-If Field Specification**: Unambiguous delay fields and actual delay baseline telemetry.
- [x] **Ground Truth Calibration**: Strict 1,225 / 1,050 / 700 / 525 distribution parity (+3 real showcase projects = 3,503 total).

---

## 6. Real Showcase Projects for Demonstration

| Project Code | Project Name | Sector & State | Delay Probability | Core Bottlenecks |
| :--- | :--- | :--- | :---: | :--- |
| **`CBIC-TN-PKG02`** | Chennai-Bengaluru Industrial Corridor - Package 2 | Industrial / Expressway (Tamil Nadu, Ranipet) | **99.35%** (Critical) | Active Madras High Court stay order (90-day impact), 340.5 Ha acquisition, 420 PAF grievances. |
| **`MAHSR-MH-PAL03`** | Mumbai-Ahmedabad High Speed Rail - Palghar Section | High-Speed Rail (Maharashtra, Palghar) | **99.75%** (Critical) | Active judicial stay order (180-day impact), 62.5% compensation disbursement rate, 890 PAFs. |
| **`BSRP-KA-CORR04`** | Bengaluru Suburban Rail Project - Corridor 4 | Rail Transit (Karnataka, Bengaluru Urban) | **1.60%** (Low) | High stakeholder responsiveness (91/100), 94.4% compensation disbursed; on track. |

---

## 7. Interactive API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/predict/{project_id}` | Real-time XGBoost risk classification & delay probability. |
| `GET` | `/api/projects/{project_id}/explain` | Local SHAP attribution breakdown (top 5 risk drivers with direction). |
| `GET` | `/api/projects/{project_id}/propagation` | Sequential delay propagation cascade across all 5 statutory RFCTLARR milestones. |
| `POST` | `/api/projects/{project_id}/what-if` | Counterfactual simulation measuring delay days saved from policy interventions. |
| `POST` | `/api/projects/{project_id}/generate-recommendation` | Gemini 2.5 Flash administrative memo synthesis & automated alert creation. |
| `GET` | `/api/projects/{project_id}/recommendations` | List of stored administrative directives and executive memos. |
| `GET` | `/api/summary` | Executive KPI overview cards and calibrated ground truth risk breakdown. |
| `GET` | `/api/districts/summary` | Spatial district-level project counts and delay risk intensity for heatmap. |
| `GET` | `/api/alerts` | Prioritized High & Critical queue sorted by live delay probability. |

---

## 8. Directory Layout

```
SIH PROTOTYPE/
├── backend/
│   ├── alembic/                # Database schema migrations
│   ├── app/
│   │   ├── models/             # SQLAlchemy ORM models (Project, Stage, Compensation, Risk, etc.)
│   │   ├── routers/            # FastAPI API route controllers (predictions, dashboard, recommendations)
│   │   └── services/           # Business logic (recommendation engine, Gemini LLM service, project lookup)
│   ├── scripts/                # Synthetic data generation, seed scripts, refresh scores, verification
│   ├── tests/                  # Automated PyTest integration test suite
│   └── requirements.txt        # Python backend dependencies
├── frontend/
│   ├── public/                 # Static assets & India District GeoJSON boundaries (dists11.geojson)
│   ├── src/
│   │   ├── api/                # API client interface (fetch wrappers with 404/422/500 handling)
│   │   ├── components/         # React UI components (DistrictHeatmap, ProjectDetail, AlertsFeed, Table)
│   │   └── index.css           # Government dashboard aesthetic styling
│   └── package.json            # Node.js dependencies (React, Vite, Recharts, Lucide)
├── ml/
│   ├── models/                 # Pre-trained binaries (.joblib) for classifier, survival, and propagation
│   ├── explain.py              # SHAP TreeExplainer local and global feature attribution
│   ├── features.py             # Feature extraction and encoding pipeline
│   ├── propagation.py          # Autoregressive sequential delay propagation models
│   └── what_if.py              # Counterfactual simulation engine
├── docs/
│   └── demo_script.md          # 5-Minute live presentation and evaluation demonstration script
├── docker-compose.yml          # PostgreSQL 16 + PostGIS service definition
├── .env.example                # Template environment variables
└── README.md                   # Platform documentation
```

---

## 9. License

Developed for the **Smart India Hackathon (SIH26017)**. Distributed under the MIT License.
