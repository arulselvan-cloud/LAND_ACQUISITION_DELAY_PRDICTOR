# LandSight AI - Data Dictionary

Comprehensive data dictionary for all relational tables, geometry columns, enums, and metrics in the **LandSight AI** PostgreSQL + PostGIS platform.

---

## 1. Table: `projects`
Stores foundational infrastructure project definitions, administrative hierarchy, spatial location, and statutory status.

| Field Name | Type | Nullable | Description | Example / Allowed Values |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | No | Primary Key | `b7e129af-46b6-4a23-8626-5a8c0d3540ca` |
| `name` | VARCHAR(255) | No | Official infrastructure project name | `Chennai-Bengaluru Industrial Corridor` |
| `project_code` | VARCHAR(50) | No | Unique business code with state prefix | `SYN-TN-0042`, `CBIC-TN-PKG02` |
| `district` | VARCHAR(100) | No | Revenue district name | `Ranipet`, `Bengaluru Urban` |
| `state` | VARCHAR(100) | No | State or Union Territory | `Tamil Nadu`, `Maharashtra` |
| `project_type` | VARCHAR(100) | No | Infrastructure asset classification | `Highway`, `Railway`, `Industrial`, `Irrigation`, `Urban Infrastructure` |
| `land_area_hectares` | FLOAT | No | Total required land acquisition area | `340.5` |
| `affected_families_count`| INTEGER | No | Number of project-affected families (PAFs)| `420` |
| `notification_date` | DATE | No | Preliminary Section 11 gazette notification date | `2024-03-15` |
| `target_possession_date` | DATE | Yes | Scheduled handover target date | `2025-06-30` |
| `actual_possession_date` | DATE | Yes | Actual physical possession handover date | `2025-11-12` |
| `status` | VARCHAR(50) | No | Global workflow status | `active`, `in_progress`, `delayed`, `completed` |
| `location` | GEOGRAPHY(Point, 4326) | Yes | Spatial geographic coordinate (WGS84) | `POINT(79.3326 12.9298)` |
| `data_source` | ENUM | No | Record provenance for hygiene tracking | `'synthetic'`, `'real'` |
| `created_at` | TIMESTAMPTZ | No | Audit creation timestamp | `2026-09-05 07:48:17+00` |
| `updated_at` | TIMESTAMPTZ | No | Audit modification timestamp | `2026-09-05 07:48:17+00` |

---

## 2. Table: `stages`
Tracks statutory milestone progression across the 5 lifecycle phases mandated under RFCTLARR Act 2013.

| Field Name | Type | Nullable | Description | Example / Allowed Values |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | No | Primary Key | `UUID` |
| `project_id` | UUID | No | Foreign Key to `projects.id` | `UUID` |
| `stage_name` | ENUM | No | Statutory lifecycle stage | `'notification'`, `'survey'`, `'compensation'`, `'possession'`, `'rehabilitation'` |
| `stage_order` | INTEGER | No | Chronological sequencing (1 to 5) | `1`, `2`, `3`, `4`, `5` |
| `planned_duration_days` | INTEGER | No | Scheduled SLA statutory duration in days | `60` |
| `actual_duration_days` | INTEGER | Yes | Actual duration elapsed in days | `130` (NULL if stage not completed) |
| `status` | ENUM | No | Milestone status | `'not_started'`, `'in_progress'`, `'completed'`, `'delayed'`, `'blocked'` |
| `start_date` | DATE | Yes | Stage inception date | `2024-04-01` |
| `target_completion_date` | DATE | Yes | Target milestone completion date | `2024-06-01` |
| `actual_completion_date` | DATE | Yes | Actual milestone completion date | `2024-08-15` |
| `delay_days` | INTEGER | No | Net overdue days beyond scheduled SLA | `75` |
| `data_source` | ENUM | No | Origin tag | `'synthetic'`, `'real'` |
| `created_at` | TIMESTAMPTZ | No | Audit creation timestamp | `TIMESTAMPTZ` |
| `updated_at` | TIMESTAMPTZ | No | Audit update timestamp | `TIMESTAMPTZ` |

---

## 3. Table: `stakeholders`
Quantifies institutional actor involvement and responsiveness to identify administrative latency bottlenecks.

| Field Name | Type | Nullable | Description | Example / Allowed Values |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | No | Primary Key | `UUID` |
| `project_id` | UUID | No | Foreign Key to `projects.id` | `UUID` |
| `name` | VARCHAR(255) | No | Official authority or organization name | `District Collector Office`, `NHAI PIU` |
| `role` | VARCHAR(100) | No | Statutory actor designation | `District Collector`, `Land Acquisition Officer`, `Project Implementing Agency`, `Gram Panchayat / Local Body` |
| `responsiveness_score` | FLOAT | No | Quantitative responsiveness index (0 to 100) | `78.5` (lower implies administrative friction) |
| `last_contact_date` | DATE | Yes | Date of most recent formal communication | `2026-08-25` |
| `notes` | TEXT | Yes | Field inspection comments or friction notes | `Understaffed revenue department surveyors` |
| `data_source` | ENUM | No | Origin tag | `'synthetic'`, `'real'` |
| `created_at` | TIMESTAMPTZ | No | Audit timestamp | `TIMESTAMPTZ` |
| `updated_at` | TIMESTAMPTZ | No | Audit timestamp | `TIMESTAMPTZ` |

---

## 4. Table: `compensation_records`
Monitors financial award determinations and disbursement metrics.

| Field Name | Type | Nullable | Description | Example / Allowed Values |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | No | Primary Key | `UUID` |
| `project_id` | UUID | No | Foreign Key to `projects.id` | `UUID` |
| `total_amount_allocated` | NUMERIC(15, 2)| No | Gross statutory award sanctioned (INR) | `145000000.00` (14.5 Cr INR) |
| `total_amount_disbursed` | NUMERIC(15, 2)| No | Actual amount credited to beneficiaries (INR)| `87000000.00` |
| `beneficiaries_count` | INTEGER | No | Total entitled titleholders | `420` |
| `disbursed_count` | INTEGER | No | Titleholders who received full award | `252` |
| `valuation_method` | VARCHAR(255) | Yes | Statutory formula applied | `Market Value x 1.5 Multiplier + 100% Solatium` |
| `status` | ENUM | No | Disbursement state | `'pending'`, `'partially_disbursed'`, `'fully_disbursed'`, `'disputed'` |
| `last_disbursement_date` | DATE | Yes | Date of latest payment tranche | `2026-08-15` |
| `notes` | TEXT | Yes | Audit notes on disbursement bottlenecks | `Consent pending for 4 tribal villages` |
| `data_source` | ENUM | No | Origin tag | `'synthetic'`, `'real'` |
| `created_at` | TIMESTAMPTZ | No | Audit timestamp | `TIMESTAMPTZ` |
| `updated_at` | TIMESTAMPTZ | No | Audit timestamp | `TIMESTAMPTZ` |

---

## 5. Table: `legal_disputes`
Captures litigation, judicial forum, contestation categories, and injunction status.

| Field Name | Type | Nullable | Description | Example / Allowed Values |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | No | Primary Key | `UUID` |
| `project_id` | UUID | No | Foreign Key to `projects.id` | `UUID` |
| `case_number` | VARCHAR(100) | No | Official court docket or suit number | `WP/MD/2491/2023`, `OS/771/2024` |
| `court_forum` | VARCHAR(100) | No | Judicial or tribunal jurisdiction | `High Court`, `District Court`, `Civil Court`, `LARR Authority` |
| `dispute_type` | VARCHAR(100) | No | Category of legal challenge | `Valuation Dispute`, `Title Contest`, `PESA / Tribal Rights`, `Environmental Clearance` |
| `stay_order_active` | BOOLEAN | No | Whether an active injunction halts work | `TRUE`, `FALSE` |
| `status` | ENUM | No | Case proceedings state | `'pending'`, `'stay_granted'`, `'hearing_scheduled'`, `'dismissed'`, `'resolved'` |
| `filed_date` | DATE | No | Date lawsuit was admitted | `2023-11-20` |
| `resolution_date` | DATE | Yes | Date judgment was pronounced | `2024-05-18` |
| `delay_impact_estimate_days`| INTEGER | No | Estimated possession days lost | `180` |
| `petitioner_name` | VARCHAR(255) | Yes | Party filing dispute | `Ranipet Farmers Association` |
| `respondent_name` | VARCHAR(255) | Yes | Government authority / implementing body | `District Collector & Competent Authority` |
| `summary` | TEXT | Yes | Key legal grounds and claims | `Challenge to circle rate multiplier determination` |
| `data_source` | ENUM | No | Origin tag | `'synthetic'`, `'real'` |
| `created_at` | TIMESTAMPTZ | No | Audit timestamp | `TIMESTAMPTZ` |
| `updated_at` | TIMESTAMPTZ | No | Audit timestamp | `TIMESTAMPTZ` |

---

## 6. Table: `rehabilitation_progress`
Tracks compliance with statutory Resettlement and Rehabilitation (R&R) schemes.

| Field Name | Type | Nullable | Description | Example / Allowed Values |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | No | Primary Key | `UUID` |
| `project_id` | UUID | No | Foreign Key to `projects.id` | `UUID` |
| `total_families_eligible` | INTEGER | No | Families entitled to R&R benefits | `180` |
| `families_resettled` | INTEGER | No | Families relocated to new housing/sites | `95` |
| `monetary_allowance_disbursed`| NUMERIC(15, 2)| No | Subsistence / transport grant disbursed | `19000000.00` |
| `alternative_land_allotted_count`| INTEGER | No | Farmers provided alternative agricultural land| `60` |
| `housing_units_constructed` | INTEGER | No | R&R colony residential units built | `110` |
| `housing_units_allotted` | INTEGER | No | R&R units physically handed over | `90` |
| `rr_scheme_status` | ENUM | No | R&R scheme approval state | `'draft'`, `'approved'`, `'in_progress'`, `'completed'` |
| `completion_percentage` | FLOAT | No | Overall R&R progress (0.0 to 100.0%) | `52.8` |
| `notes` | TEXT | Yes | Township infrastructure completion notes | `Community center and school 80% finished` |
| `data_source` | ENUM | No | Origin tag | `'synthetic'`, `'real'` |
| `created_at` | TIMESTAMPTZ | No | Audit timestamp | `TIMESTAMPTZ` |
| `updated_at` | TIMESTAMPTZ | No | Audit timestamp | `TIMESTAMPTZ` |

---

## 7. Table: `risk_scores`
Stores Machine Learning delay predictions, per-stage risk probabilities, and SHAP explainability weights.

| Field Name | Type | Nullable | Description | Example / Allowed Values |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | No | Primary Key | `UUID` |
| `project_id` | UUID | No | Foreign Key to `projects.id` | `UUID` |
| `risk_category` | ENUM | No | Categorical risk rating | `'low'`, `'medium'`, `'high'`, `'critical'` |
| `overall_delay_probability`| FLOAT | No | Calibrated delay probability (0.0 to 1.0)| `0.84` |
| `stage_delay_probabilities`| JSONB | No | Probability of delay breakdown across stages| `{"notification": 0.05, "survey": 0.32, "compensation": 0.88, "possession": 0.85, "rehabilitation": 0.62}` |
| `predicted_delay_days` | INTEGER | No | Forecasted delay beyond target possession | `145` |
| `confidence_score` | FLOAT | Yes | Model prediction confidence | `0.92` |
| `top_risk_drivers` | JSONB | Yes | SHAP feature importance & factor weights | `[{"factor": "stay_order_active", "impact": 0.42}]` |
| `computed_at` | TIMESTAMPTZ | No | Timestamp when inference was executed | `TIMESTAMPTZ` |
| `data_source` | ENUM | No | Origin tag | `'synthetic'`, `'real'` |
| `created_at` | TIMESTAMPTZ | No | Audit timestamp | `TIMESTAMPTZ` |
| `updated_at` | TIMESTAMPTZ | No | Audit timestamp | `TIMESTAMPTZ` |
