# Land Acquisition Delay Predictor - Architecture Overview

## Problem Statement
**SIH26017**: AI-Powered Predictive Analytics Platform for Early Detection of Land Acquisition Delays.

## System Architecture

```
+-------------------------------------------------------------+
|                  React Dashboard (Vite)                     |
|           - Interactive GIS Parcel Map                      |
|           - Delay Risk Assessment Scorecards                |
|           - SHAP Explainability & Feature Contribution      |
+------------------------------+------------------------------+
                               | REST API / WebSockets
                               v
+-------------------------------------------------------------+
|                   FastAPI Backend Service                   |
|   +---------------------+        +----------------------+   |
|   | Routers:            |        | Services:            |   |
|   | - /parcels          |        | - Delay Predictor    |   |
|   | - /predictions      |        | - Spatial Analytics  |   |
|   | - /analytics        |        | - SHAP Explainer     |   |
|   +----------+----------+        +----------+-----------+   |
|              |                              |               |
|              +--------------+---------------+               |
|                             v                               |
|                  SQLAlchemy ORM Layer                       |
+------------------------------+------------------------------+
                               |
              +----------------+----------------+
              |                                 |
              v                                 v
+-------------------------------+ +---------------------------+
| PostgreSQL + PostGIS Database | | ML Inference Engine       |
| - Spatial parcel boundaries   | | - XGBoost / LightGBM      |
| - Statutory milestones        | | - Cox Proportional Hazard |
| - Dispute records             | | - SHAP Value Computer     |
+-------------------------------+ +---------------------------+
```

## Core Modules
1. **Data Ingestion & Feature Store (`data/`)**: Gazette records, cadastral surveys, land classification, and temporal milestones.
2. **Machine Learning Pipeline (`ml/`)**:
   - Delay Classification (Risk severity: Low / Medium / High / Critical)
   - Survival Analysis (Time-to-acquisition completion)
   - Explainable AI (SHAP value breakdown for administrative stakeholders)
3. **API Service (`backend/`)**: FastAPI endpoints for spatial querying, prediction serving, and simulation.
4. **Interactive Dashboard (`frontend/`)**: React-based geospatial interface with heatmaps and actionable intervention insights.

## Known Limitations

- **Authentication and Role-Based Access Control (RBAC)**: Explicitly identified in SIH26017's problem statement, authentication and multi-tier role-based access control are not implemented in this prototype due to hackathon time constraints. In a production enterprise deployment, role-based access control would be established with dedicated access tiers for:
  1. **District Administration**: Field-level data updates, survey milestone logging, and parcel dispute resolutions.
  2. **State Governments**: State-wide cross-project monitoring, compensation disbursement oversight, and inter-departmental clearances.
  3. **Central Ministries**: National oversight dashboard, infrastructure corridor bottleneck tracking, and macro capital allocation.
