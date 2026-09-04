# Data Assumptions & Data Dictionary (SIH26017)

## Overview
This document outlines the data structure, assumptions, and feature dictionary for the **LandSight AI** platform (SIH26017: AI-powered predictive analytics platform for early detection of land acquisition delays).

---

## 1. Data Sources & Ingestion Assumptions

### 1.1 Datasets
- **Raw Datasets**: Government gazette notifications (e.g., Section 4, 6, 11 notifications under RFCTLARR / relevant acts), cadastral survey data, GIS boundary shapefiles/GeoJSON, compensation disbursement records, court dispute logs.
- **Synthetic Datasets**: Simulated multi-district project timelines with varying geographical complexities, dispute densities, and regulatory bottlenecks to augment training when historical acquisition records have sparse labels.

### 1.2 Core Assumptions
1. **Temporal Milestones**: Land acquisition processes follow defined statutory milestones (Preliminary Notification, Joint Measurement Survey, Valuation, Draft Declaration, Rehabilitation & Resettlement Scheme, Award Declaration, Physical Possession).
2. **Dispute Resolution Latency**: Legal challenges and title disputes exponentially correlate with physical possession delays.
3. **Data Completeness**: Missing milestone dates are handled using right-censoring in survival analysis models rather than naive imputation.
4. **Spatial Correlation**: Contiguous parcels within a revenue village or taluk share correlated environmental and socio-political risk profiles.

---

## 2. Preliminary Data Dictionary

| Field Name | Type | Description | Example / Values |
| :--- | :--- | :--- | :--- |
| `parcel_id` | String / UUID | Unique parcel or survey number identifier | `PAR-TN-2024-0012` |
| `project_id` | String / UUID | Infrastructure project identifier | `PRJ-NHAI-042` |
| `state` | String | State / Jurisdiction | `Tamil Nadu` |
| `district` | String | Administrative district | `Kanchipuram` |
| `land_category` | Categorical | Land use classification | `Agricultural`, `Commercial`, `Residential`, `Wetland`, `Forest` |
| `area_hectares` | Float | Total area of parcel in hectares | `1.45` |
| `encumbrance_status` | Boolean | Whether an active legal dispute/encumbrance exists | `True` / `False` |
| `num_owners` | Integer | Total title holders / interested parties | `3` |
| `rr_required` | Boolean | Resettlement & Rehabilitation required | `True` / `False` |
| `notif_date` | Date | Date of preliminary section notification | `2023-04-15` |
| `possession_target_date`| Date | Scheduled possession handover date | `2024-04-15` |
| `actual_possession_date`| Date | Actual possession handover date (or null) | `2024-09-20` |
| `delay_days` | Integer | Calculated days beyond target possession date | `158` |
| `delay_risk_category` | Categorical | Target classification label | `Low`, `Medium`, `High`, `Critical` |

---

## 3. Data Storage & Formats
- `data/raw/`: Read-only source files, gazette dumps, shapefiles.
- `data/synthetic/`: Algorithmic mock datasets for survival analysis & regression tests.
- `data/processed/`: Normalized feature tables ready for model training.
