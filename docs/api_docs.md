# Land Acquisition Delay Predictor - API Specification (Draft)

## Base URL
```
http://localhost:8000/api/v1
```

## Planned Endpoints

### 1. Health & Status
- `GET /health` - Service health verification.

### 2. Parcels & Spatial Queries
- `GET /parcels` - List land parcels with pagination and filter criteria.
- `GET /parcels/{parcel_id}` - Retrieve details, boundaries (GeoJSON), and milestone history for a specific parcel.
- `GET /parcels/geojson` - Retrieve GeoJSON FeatureCollection for map rendering.

### 3. Predictive Analytics
- `POST /predictions/predict-delay` - Predict probability of delay and risk category for a parcel or project batch.
- `GET /predictions/{parcel_id}/explain` - Retrieve SHAP explanation feature contributions for a predicted delay.
- `POST /predictions/survival-curve` - Generate Cox proportional hazards time-to-completion curve.

### 4. Mitigation & What-If Simulation
- `POST /analytics/simulate-intervention` - Model the impact of accelerated dispute settlement or compensation adjustments on project completion timelines.
