"""LandSight AI - Synthetic Dataset Generator (RFCTLARR Act 2013 Distributions).

Generates 3,000 - 5,000 realistic Indian infrastructure land acquisition projects with correlated
delays using a saturated logistic/sigmoid risk formulation and percentile-based risk categorizations.

Target Risk Distribution:
    Low:      ~35% (0 - 35 days delay)
    Medium:   ~30% (35 - 95 days delay)
    High:     ~20% (95 - 220 days delay)
    Critical: ~15% (220 - 700+ days delay)

Usage:
    python backend/scripts/generate_synthetic_dataset.py [--count 3500] [--batch-size 500] [--seed 42]
"""

import argparse
import datetime
import json
import math
import os
import random
import subprocess
import sys
import uuid
from collections import Counter
from pathlib import Path

import numpy as np
from geoalchemy2.elements import WKTElement

# Add project root and backend to sys.path
backend_dir = Path(__file__).resolve().parents[1]
root_dir = backend_dir.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(backend_dir))

from backend.app.database import SessionLocal, engine
from backend.app.models import (
    Alert,
    AlertSeverityEnum,
    CompensationRecord,
    CompensationStatusEnum,
    DataSourceEnum,
    DisputeStatusEnum,
    LegalDispute,
    PriorityEnum,
    Project,
    Recommendation,
    RehabilitationProgress,
    RiskCategoryEnum,
    RiskScore,
    RRSchemeStatusEnum,
    Stage,
    StageNameEnum,
    StageStatusEnum,
    Stakeholder,
)

# ---------------------------------------------------------------------------
# Indian Administrative & Spatial Reference Catalog
# ---------------------------------------------------------------------------

INDIAN_STATES = {
    "TN": {
        "state": "Tamil Nadu",
        "districts": [
            {"district": "Ranipet", "center": (79.33, 12.93), "tribal": False},
            {"district": "Kanchipuram", "center": (79.70, 12.83), "tribal": False},
            {"district": "Salem", "center": (78.14, 11.66), "tribal": False},
            {"district": "Coimbatore", "center": (76.96, 11.01), "tribal": False},
            {"district": "Tiruvallur", "center": (79.91, 13.14), "tribal": False},
        ],
    },
    "KA": {
        "state": "Karnataka",
        "districts": [
            {"district": "Bengaluru Urban", "center": (77.59, 12.97), "tribal": False},
            {"district": "Bengaluru Rural", "center": (77.71, 13.23), "tribal": False},
            {"district": "Tumakuru", "center": (77.10, 13.34), "tribal": False},
            {"district": "Mysuru", "center": (76.64, 12.30), "tribal": False},
            {"district": "Belagavi", "center": (74.50, 15.85), "tribal": False},
        ],
    },
    "MH": {
        "state": "Maharashtra",
        "districts": [
            {"district": "Palghar", "center": (72.77, 19.70), "tribal": True},
            {"district": "Thane", "center": (72.98, 19.22), "tribal": False},
            {"district": "Pune", "center": (73.85, 18.52), "tribal": False},
            {"district": "Nagpur", "center": (79.09, 21.15), "tribal": False},
            {"district": "Nashik", "center": (73.79, 20.00), "tribal": False},
        ],
    },
    "GJ": {
        "state": "Gujarat",
        "districts": [
            {"district": "Ahmedabad", "center": (72.57, 23.02), "tribal": False},
            {"district": "Surat", "center": (72.83, 21.17), "tribal": False},
            {"district": "Vadodara", "center": (73.18, 22.30), "tribal": False},
            {"district": "Bharuch", "center": (72.99, 21.71), "tribal": False},
        ],
    },
    "UP": {
        "state": "Uttar Pradesh",
        "districts": [
            {"district": "Varanasi", "center": (82.97, 25.32), "tribal": False},
            {"district": "Gautam Buddha Nagar", "center": (77.40, 28.53), "tribal": False},
            {"district": "Lucknow", "center": (80.95, 26.85), "tribal": False},
            {"district": "Agra", "center": (78.01, 27.18), "tribal": False},
            {"district": "Prayagraj", "center": (81.85, 25.43), "tribal": False},
        ],
    },
    "AP": {
        "state": "Andhra Pradesh",
        "districts": [
            {"district": "Visakhapatnam", "center": (83.22, 17.69), "tribal": False},
            {"district": "Guntur", "center": (80.44, 16.31), "tribal": False},
            {"district": "Krishna", "center": (80.82, 16.18), "tribal": False},
            {"district": "Chittoor", "center": (79.10, 13.22), "tribal": False},
        ],
    },
    "OD": {
        "state": "Odisha",
        "districts": [
            {"district": "Jharsuguda", "center": (84.01, 21.86), "tribal": True},
            {"district": "Sundargarh", "center": (84.04, 22.12), "tribal": True},
            {"district": "Sambalpur", "center": (83.98, 21.47), "tribal": False},
            {"district": "Mayurbhanj", "center": (86.73, 21.93), "tribal": True},
        ],
    },
    "RJ": {
        "state": "Rajasthan",
        "districts": [
            {"district": "Jaipur", "center": (75.79, 26.91), "tribal": False},
            {"district": "Jodhpur", "center": (73.02, 26.24), "tribal": False},
            {"district": "Alwar", "center": (76.61, 27.55), "tribal": False},
            {"district": "Udaipur", "center": (73.71, 24.59), "tribal": True},
        ],
    },
    "MP": {
        "state": "Madhya Pradesh",
        "districts": [
            {"district": "Indore", "center": (75.86, 22.72), "tribal": False},
            {"district": "Bhopal", "center": (77.41, 23.26), "tribal": False},
            {"district": "Jabalpur", "center": (79.93, 23.18), "tribal": False},
            {"district": "Mandla", "center": (80.38, 22.60), "tribal": True},
        ],
    },
    "WB": {
        "state": "West Bengal",
        "districts": [
            {"district": "Paschim Bardhaman", "center": (86.98, 23.69), "tribal": False},
            {"district": "Purba Medinipur", "center": (87.75, 22.00), "tribal": False},
            {"district": "North 24 Parganas", "center": (88.52, 22.72), "tribal": False},
            {"district": "Howrah", "center": (88.26, 22.59), "tribal": False},
        ],
    },
    "BR": {
        "state": "Bihar",
        "districts": [
            {"district": "Patna", "center": (85.14, 25.61), "tribal": False},
            {"district": "Gaya", "center": (84.99, 24.80), "tribal": False},
            {"district": "Muzaffarpur", "center": (85.40, 26.12), "tribal": False},
            {"district": "Bhagalpur", "center": (86.98, 25.25), "tribal": False},
        ],
    },
    "TS": {
        "state": "Telangana",
        "districts": [
            {"district": "Rangareddy", "center": (78.55, 17.34), "tribal": False},
            {"district": "Hyderabad", "center": (78.48, 17.39), "tribal": False},
            {"district": "Warangal", "center": (79.60, 17.98), "tribal": False},
            {"district": "Medak", "center": (78.26, 18.05), "tribal": False},
        ],
    },
}

PROJECT_TYPES = [
    ("Highway", 0.35),
    ("Railway", 0.25),
    ("Industrial", 0.15),
    ("Irrigation", 0.15),
    ("Urban Infrastructure", 0.10),
]

COURT_FORUMS = [
    "High Court",
    "District Civil Court",
    "Land Acquisition Rehabilitation & Resettlement Authority",
    "National Green Tribunal",
    "Supreme Court of India",
]

DISPUTE_TYPES = [
    "Valuation Multiplier Dispute",
    "Ancestral Title & Partition Contestation",
    "Ownership Encroachment Claim",
    "PESA / Tribal Gram Sabha Consent Deadlock",
    "Environmental Clearance & Forest Rights Challenge",
]


def generate_candidate_features(seq_id: int, today: datetime.date):
    """Generates the underlying physical, socio-economic, and legal attributes of a project."""
    state_code = random.choice(list(INDIAN_STATES.keys()))
    state_meta = INDIAN_STATES[state_code]
    district_meta = random.choice(state_meta["districts"])

    proj_type = random.choices(
        [t[0] for t in PROJECT_TYPES],
        weights=[t[1] for t in PROJECT_TYPES],
    )[0]

    code = f"SYN-{state_code}-{seq_id:04d}"
    name = f"{state_meta['state']} {district_meta['district']} {proj_type} Project - Phase {random.randint(1, 4)}"

    base_lon, base_lat = district_meta["center"]
    lon = round(base_lon + random.gauss(0, 0.06), 6)
    lat = round(base_lat + random.gauss(0, 0.06), 6)
    location_wkt = f"POINT({lon} {lat})"

    area = round(float(np.clip(np.random.lognormal(mean=4.2, sigma=0.85), 8.0, 1500.0)), 2)

    density_mult = {
        "Urban Infrastructure": random.uniform(6.0, 14.0),
        "Highway": random.uniform(1.8, 4.0),
        "Railway": random.uniform(1.5, 3.8),
        "Industrial": random.uniform(0.9, 2.2),
        "Irrigation": random.uniform(0.6, 1.8),
    }[proj_type]
    families = int(area * density_mult * random.uniform(0.8, 1.3)) + random.randint(5, 30)

    notif_days_ago = random.randint(200, 900)
    notif_date = today - datetime.timedelta(days=notif_days_ago)

    # Risk signals
    has_dispute = random.random() < 0.25
    stay_active = has_dispute and (random.random() < 0.45)

    is_tribal_pesa = district_meta["tribal"] and (random.random() < 0.65)
    if not is_tribal_pesa and random.random() < 0.08:
        is_tribal_pesa = True

    disbursement_pct = float(np.clip(np.random.beta(a=3.5, b=2.5), 0.05, 0.98))

    # Stakeholders
    num_stk = random.choice([2, 3])
    stk_roles = [
        "District Collector",
        "Special Land Acquisition Officer (SLAO)",
        "Project Implementing Agency",
        "Gram Panchayat / Local Body",
    ]
    random.shuffle(stk_roles)
    stakeholders = []
    stk_scores = []
    for r_idx in range(num_stk):
        role = stk_roles[r_idx]
        if is_tribal_pesa and role == "Gram Panchayat / Local Body":
            base_score = random.uniform(30.0, 52.0)
        elif has_dispute and role == "Special Land Acquisition Officer (SLAO)":
            base_score = random.uniform(45.0, 68.0)
        else:
            base_score = random.uniform(55.0, 95.0)

        stk_score = round(base_score, 1)
        stk_scores.append(stk_score)
        stakeholders.append({
            "name": f"{role} Office - {district_meta['district']}",
            "role": role,
            "responsiveness_score": stk_score,
            "last_contact_date": today - datetime.timedelta(days=random.randint(2, 45)),
            "notes": f"Statutory workflow stakeholder for {proj_type} parcel acquisition.",
            "data_source": DataSourceEnum.synthetic,
        })
    avg_stk_score = sum(stk_scores) / len(stk_scores)

    # ---------------------------------------------------------------------------
    # Logistic / Sigmoid Multi-Factor Formulation (Saturating, non-linear)
    # ---------------------------------------------------------------------------
    x_dispute = 1.0 if stay_active else (0.55 if has_dispute else 0.0)
    x_comp = max(0.0, 1.0 - disbursement_pct) ** 1.3
    x_stk = max(0.0, (75.0 - avg_stk_score) / 75.0)
    x_pesa = 1.0 if is_tribal_pesa else 0.0
    x_fam = math.log1p(families) / math.log1p(2500.0)

    # Saturated logit combination
    logit = -2.25 + (1.95 * x_dispute) + (1.85 * x_comp) + (1.40 * x_stk) + (1.25 * x_pesa) + (0.90 * x_fam) + random.gauss(0, 0.20)
    raw_risk_score = 1.0 / (1.0 + math.exp(-logit))

    return {
        "seq_id": seq_id,
        "state_code": state_code,
        "state_name": state_meta["state"],
        "district": district_meta["district"],
        "proj_type": proj_type,
        "name": name,
        "code": code,
        "location_wkt": location_wkt,
        "area": area,
        "families": families,
        "notif_date": notif_date,
        "has_dispute": has_dispute,
        "stay_active": stay_active,
        "is_tribal_pesa": is_tribal_pesa,
        "disbursement_pct": disbursement_pct,
        "stakeholders": stakeholders,
        "avg_stk_score": avg_stk_score,
        "raw_risk_score": raw_risk_score,
    }


def build_full_record(feat: dict, risk_cat: RiskCategoryEnum, today: datetime.date):
    """Builds complete relational payload calibrated to assigned risk category."""
    raw_score = feat["raw_risk_score"]

    # Map delay days monotonically according to risk category with realistic variance
    if risk_cat == RiskCategoryEnum.low:
        total_delay_days = int(random.uniform(0, 35))
        overall_prob = round(random.uniform(0.05, 0.28), 3)
    elif risk_cat == RiskCategoryEnum.medium:
        total_delay_days = int(random.uniform(36, 95))
        overall_prob = round(random.uniform(0.29, 0.52), 3)
    elif risk_cat == RiskCategoryEnum.high:
        total_delay_days = int(random.uniform(96, 220))
        overall_prob = round(random.uniform(0.53, 0.76), 3)
    else:  # Critical
        # Heavy tail for critical delays
        total_delay_days = int(random.uniform(221, 550) + (random.uniform(0, 200) if feat["stay_active"] else 0))
        overall_prob = round(random.uniform(0.77, 0.98), 3)

    # 1. 5 Statutory Stages
    stage_templates = [
        (StageNameEnum.notification, 1, random.randint(45, 90), 0.03),
        (StageNameEnum.survey, 2, random.randint(60, 120), 0.12),
        (StageNameEnum.compensation, 3, random.randint(90, 180), 0.40),
        (StageNameEnum.possession, 4, random.randint(60, 120), 0.32),
        (StageNameEnum.rehabilitation, 5, random.randint(120, 240), 0.13),
    ]

    stages_data = []
    for s_name, s_order, planned_days, weight in stage_templates:
        stage_delay = int(total_delay_days * weight)
        actual_days = planned_days + stage_delay

        if s_order == 1:
            status = StageStatusEnum.completed
            actual_duration = actual_days
        elif s_order == 2:
            status = StageStatusEnum.completed if total_delay_days < 250 else StageStatusEnum.delayed
            actual_duration = actual_days if status == StageStatusEnum.completed else None
        elif s_order in (3, 4):
            if stage_delay > 45:
                status = StageStatusEnum.delayed
            elif stage_delay > 0:
                status = StageStatusEnum.in_progress
            else:
                status = StageStatusEnum.completed if total_delay_days == 0 else StageStatusEnum.in_progress
            actual_duration = actual_days if status == StageStatusEnum.completed else None
        else:
            status = StageStatusEnum.in_progress if feat["families"] > 50 else StageStatusEnum.completed
            actual_duration = actual_days if status == StageStatusEnum.completed else None

        stages_data.append({
            "stage_name": s_name,
            "stage_order": s_order,
            "planned_duration_days": planned_days,
            "actual_duration_days": actual_duration,
            "status": status,
            "delay_days": stage_delay,
            "data_source": DataSourceEnum.synthetic,
        })

    # 2. Compensation Record
    cost_per_hectare = random.uniform(350000.0, 1800000.0)
    total_allocated = round(feat["area"] * cost_per_hectare, 2)
    total_disbursed = round(total_allocated * feat["disbursement_pct"], 2)
    disbursed_count = int(feat["families"] * feat["disbursement_pct"])

    comp_status = CompensationStatusEnum.fully_disbursed if feat["disbursement_pct"] >= 0.95 else (
        CompensationStatusEnum.partially_disbursed if feat["disbursement_pct"] >= 0.20 else CompensationStatusEnum.pending
    )
    if feat["has_dispute"] and random.random() < 0.35:
        comp_status = CompensationStatusEnum.disputed

    comp_data = {
        "total_amount_allocated": total_allocated,
        "total_amount_disbursed": total_disbursed,
        "beneficiaries_count": feat["families"],
        "disbursed_count": disbursed_count,
        "valuation_method": f"RFCTLARR Act 2013 Multiplied Matrix x {random.choice([1.25, 1.5, 2.0])} + 100% Solatium",
        "status": comp_status,
        "last_disbursement_date": today - datetime.timedelta(days=random.randint(5, 60)),
        "notes": f"Disbursement progress at {feat['disbursement_pct'] * 100:.1f}%.",
        "data_source": DataSourceEnum.synthetic,
    }

    # 3. Legal Disputes
    disputes_data = []
    if feat["has_dispute"]:
        d_status = DisputeStatusEnum.stay_granted if feat["stay_active"] else random.choice([
            DisputeStatusEnum.pending,
            DisputeStatusEnum.hearing_scheduled,
        ])
        disp_type = "PESA / Tribal Gram Sabha Consent Deadlock" if feat["is_tribal_pesa"] else random.choice(DISPUTE_TYPES)
        disputes_data.append({
            "case_number": f"WP/{feat['state_code']}/{random.randint(1000, 9999)}/{today.year - random.randint(0, 2)}",
            "court_forum": random.choice(COURT_FORUMS),
            "dispute_type": disp_type,
            "stay_order_active": feat["stay_active"],
            "status": d_status,
            "filed_date": today - datetime.timedelta(days=random.randint(60, 450)),
            "delay_impact_estimate_days": int(total_delay_days * 0.45),
            "petitioner_name": f"{feat['district']} Landowners Action Committee",
            "respondent_name": f"State Revenue Department & {feat['proj_type']} Authority",
            "summary": f"Litigation challenging land valuation and award declaration in {feat['district']}.",
            "data_source": DataSourceEnum.synthetic,
        })

    # 4. Rehabilitation Progress
    resettled_pct = random.uniform(0.20, 0.95) if feat["families"] > 0 else 1.0
    families_resettled = int(feat["families"] * resettled_pct)
    rr_status = RRSchemeStatusEnum.completed if resettled_pct >= 0.90 else RRSchemeStatusEnum.in_progress
    rr_data = {
        "total_families_eligible": feat["families"],
        "families_resettled": families_resettled,
        "monetary_allowance_disbursed": round(families_resettled * random.uniform(40000.0, 120000.0), 2),
        "alternative_land_allotted_count": int(families_resettled * random.uniform(0.1, 0.4)),
        "housing_units_constructed": int(feat["families"] * random.uniform(0.7, 1.1)),
        "housing_units_allotted": families_resettled,
        "rr_scheme_status": rr_status,
        "completion_percentage": round(resettled_pct * 100.0, 1),
        "notes": f"R&R implementation at {resettled_pct * 100:.1f}%.",
        "data_source": DataSourceEnum.synthetic,
    }

    # 5. Risk Scores & Stage Probabilities
    stage_probs = {
        "notification": round(float(np.clip(overall_prob * 0.15, 0.02, 0.40)), 2),
        "survey": round(float(np.clip(overall_prob * 0.35, 0.05, 0.70)), 2),
        "compensation": round(float(np.clip(overall_prob * 0.95, 0.10, 0.98)), 2),
        "possession": round(float(np.clip(overall_prob * 1.05, 0.12, 0.99)), 2),
        "rehabilitation": round(float(np.clip(overall_prob * 0.70, 0.08, 0.92)), 2),
    }

    drivers = []
    if feat["has_dispute"]:
        drivers.append({"factor": "stay_order_active", "impact": round(random.uniform(0.35, 0.48), 2), "desc": "Judicial stay order halting possession"})
    if feat["disbursement_pct"] < 0.60:
        drivers.append({"factor": "compensation_disbursement_gap", "impact": round(random.uniform(0.22, 0.38), 2), "desc": f"Disbursement lagging at {feat['disbursement_pct'] * 100:.1f}%"})
    if feat["is_tribal_pesa"]:
        drivers.append({"factor": "tribal_pesa_clearance", "impact": round(random.uniform(0.25, 0.42), 2), "desc": "Fifth Schedule Gram Sabha consensus required"})
    if feat["avg_stk_score"] < 60.0:
        drivers.append({"factor": "low_stakeholder_responsiveness", "impact": round(random.uniform(0.15, 0.28), 2), "desc": f"Low stakeholder responsiveness ({feat['avg_stk_score']:.1f})"})
    if not drivers:
        drivers.append({"factor": "normal_statutory_flow", "impact": 0.10, "desc": "Standard statutory progression without critical bottlenecks"})

    risk_data = {
        "risk_category": risk_cat,
        "overall_delay_probability": overall_prob,
        "stage_delay_probabilities": stage_probs,
        "predicted_delay_days": total_delay_days,
        "confidence_score": round(random.uniform(0.85, 0.96), 2),
        "top_risk_drivers": drivers,
        "computed_at": today - datetime.timedelta(days=random.randint(1, 14)),
        "data_source": DataSourceEnum.synthetic,
    }

    project_data = {
        "name": feat["name"],
        "project_code": feat["code"],
        "district": feat["district"],
        "state": feat["state_name"],
        "project_type": feat["proj_type"],
        "land_area_hectares": feat["area"],
        "affected_families_count": feat["families"],
        "notification_date": feat["notif_date"],
        "target_possession_date": feat["notif_date"] + datetime.timedelta(days=random.randint(365, 730)),
        "status": "delayed" if total_delay_days > 90 else ("in_progress" if total_delay_days > 0 else "active"),
        "location": feat["location_wkt"],
        "data_source": DataSourceEnum.synthetic,
    }

    return {
        "project": project_data,
        "stages": stages_data,
        "compensation": comp_data,
        "disputes": disputes_data,
        "rehabilitation": rr_data,
        "stakeholders": feat["stakeholders"],
        "risk_score": risk_data,
        "total_delay_days": total_delay_days,
        "risk_category": risk_cat,
    }


def generate_and_insert(count: int = 3500, batch_size: int = 500, seed: int = 42, dry_run: bool = False):
    """Generates synthetic dataset and inserts into PostgreSQL schema in efficient batches."""
    random.seed(seed)
    np.random.seed(seed)
    today = datetime.date.today()

    print(f"\n=======================================================")
    print(f" LandSight AI - Synthetic Dataset Generation Engine")
    print(f" Target Projects: {count} | Batch Size: {batch_size} | Seed: {seed}")
    print(f" Target Risk Spread: Low ~35% | Med ~30% | High ~20% | Critical ~15%")
    print(f"=======================================================\n")

    session = SessionLocal()

    # Step 1: Clean previous synthetic records (preserves data_source = 'real')
    if not dry_run:
        print("[*] Purging previous synthetic records (keeping 'real' showcase records untouched)...")
        session.query(Project).filter(Project.data_source == DataSourceEnum.synthetic).delete(synchronize_session=False)
        session.commit()

        # Also purge synthetic in Docker container
        subprocess.run(
            ["docker", "exec", "-i", "landsight-postgis", "psql", "-U", "landsight_admin", "-d", "landsight_ai", "-c", "DELETE FROM projects WHERE data_source = 'synthetic';"],
            capture_output=True,
        )
        print("[+] Previous synthetic records purged cleanly.")

    # Step 2: Generate all candidate features to calibrate exact percentiles
    print(f"[*] Simulating multi-factor sigmoid logits for {count} projects...")
    candidates = []
    raw_scores = []
    for idx in range(count):
        feat = generate_candidate_features(idx + 1, today)
        candidates.append(feat)
        raw_scores.append(feat["raw_risk_score"])

    # Step 3: Compute exact percentiles to hit target distribution: Low ~35%, Med ~30%, High ~20%, Critical ~15%
    raw_scores_arr = np.array(raw_scores)
    t_low = float(np.percentile(raw_scores_arr, 35.0))
    t_med = float(np.percentile(raw_scores_arr, 65.0))
    t_high = float(np.percentile(raw_scores_arr, 85.0))

    print(f"[*] Calibrated Sigmoid Thresholds:")
    print(f"    Low cutoff (35th pct):       {t_low:.4f}")
    print(f"    Medium cutoff (65th pct):    {t_med:.4f}")
    print(f"    High cutoff (85th pct):      {t_high:.4f}")

    total_projects = 0
    total_stages = 0
    total_comps = 0
    total_disputes = 0
    total_rehabs = 0
    total_stks = 0
    total_risks = 0

    delay_days_list = []
    risk_categories_list = []

    # Step 4: Batch insertion into DB and live Docker container sync
    for b_start in range(0, count, batch_size):
        b_end = min(b_start + batch_size, count)
        chunk_size = b_end - b_start
        print(f"[*] Building and staging batch {b_start + 1} to {b_end} ({chunk_size} projects)...")
        sql_batch = ["BEGIN;"]

        for idx in range(b_start, b_end):
            feat = candidates[idx]
            s = feat["raw_risk_score"]
            if s <= t_low:
                r_cat = RiskCategoryEnum.low
            elif s <= t_med:
                r_cat = RiskCategoryEnum.medium
            elif s <= t_high:
                r_cat = RiskCategoryEnum.high
            else:
                r_cat = RiskCategoryEnum.critical

            rec = build_full_record(feat, r_cat, today)
            proj_id = uuid.uuid4()
            p_data = rec["project"]
            loc_wkt = p_data["location"]

            # Project
            proj = Project(
                id=proj_id,
                name=p_data["name"],
                project_code=p_data["project_code"],
                district=p_data["district"],
                state=p_data["state"],
                project_type=p_data["project_type"],
                land_area_hectares=p_data["land_area_hectares"],
                affected_families_count=p_data["affected_families_count"],
                notification_date=p_data["notification_date"],
                target_possession_date=p_data["target_possession_date"],
                status=p_data["status"],
                location=WKTElement(loc_wkt, srid=4326),
                data_source=DataSourceEnum.synthetic,
            )
            session.add(proj)
            total_projects += 1

            esc_name = p_data["name"].replace("'", "''")
            sql_batch.append(
                f"INSERT INTO projects (id, created_at, updated_at, data_source, name, project_code, district, state, project_type, land_area_hectares, affected_families_count, notification_date, target_possession_date, status, location) "
                f"VALUES ('{proj_id}', now(), now(), 'synthetic', '{esc_name}', '{p_data['project_code']}', '{p_data['district']}', '{p_data['state']}', '{p_data['project_type']}', {p_data['land_area_hectares']}, {p_data['affected_families_count']}, '{p_data['notification_date']}', '{p_data['target_possession_date']}', '{p_data['status']}', ST_GeogFromText('{loc_wkt}')) "
                f"ON CONFLICT (project_code) DO NOTHING;"
            )

            # Stages
            for stg in rec["stages"]:
                stg_id = uuid.uuid4()
                stage = Stage(
                    id=stg_id,
                    project_id=proj_id,
                    stage_name=stg["stage_name"],
                    stage_order=stg["stage_order"],
                    planned_duration_days=stg["planned_duration_days"],
                    actual_duration_days=stg["actual_duration_days"],
                    status=stg["status"],
                    delay_days=stg["delay_days"],
                    data_source=DataSourceEnum.synthetic,
                )
                session.add(stage)
                total_stages += 1

                act_val = stg["actual_duration_days"] if stg["actual_duration_days"] is not None else "NULL"
                sql_batch.append(
                    f"INSERT INTO stages (id, created_at, updated_at, data_source, project_id, stage_name, stage_order, planned_duration_days, actual_duration_days, status, delay_days) "
                    f"VALUES ('{stg_id}', now(), now(), 'synthetic', '{proj_id}', '{stg['stage_name'].value}', {stg['stage_order']}, {stg['planned_duration_days']}, {act_val}, '{stg['status'].value}', {stg['delay_days']}) "
                    f"ON CONFLICT (project_id, stage_name) DO NOTHING;"
                )

            # Compensation Record
            c = rec["compensation"]
            comp_id = uuid.uuid4()
            comp = CompensationRecord(
                id=comp_id,
                project_id=proj_id,
                total_amount_allocated=c["total_amount_allocated"],
                total_amount_disbursed=c["total_amount_disbursed"],
                beneficiaries_count=c["beneficiaries_count"],
                disbursed_count=c["disbursed_count"],
                valuation_method=c["valuation_method"],
                status=c["status"],
                last_disbursement_date=c["last_disbursement_date"],
                notes=c["notes"],
                data_source=DataSourceEnum.synthetic,
            )
            session.add(comp)
            total_comps += 1

            esc_notes = c["notes"].replace("'", "''")
            esc_val_method = c["valuation_method"].replace("'", "''")
            sql_batch.append(
                f"INSERT INTO compensation_records (id, created_at, updated_at, data_source, project_id, total_amount_allocated, total_amount_disbursed, beneficiaries_count, disbursed_count, valuation_method, status, last_disbursement_date, notes) "
                f"VALUES ('{comp_id}', now(), now(), 'synthetic', '{proj_id}', {c['total_amount_allocated']}, {c['total_amount_disbursed']}, {c['beneficiaries_count']}, {c['disbursed_count']}, '{esc_val_method}', '{c['status'].value}', '{c['last_disbursement_date']}', '{esc_notes}');"
            )

            # Legal Disputes
            for d in rec["disputes"]:
                disp_id = uuid.uuid4()
                disp = LegalDispute(
                    id=disp_id,
                    project_id=proj_id,
                    case_number=d["case_number"],
                    court_forum=d["court_forum"],
                    dispute_type=d["dispute_type"],
                    stay_order_active=d["stay_order_active"],
                    status=d["status"],
                    filed_date=d["filed_date"],
                    delay_impact_estimate_days=d["delay_impact_estimate_days"],
                    petitioner_name=d["petitioner_name"],
                    respondent_name=d["respondent_name"],
                    summary=d["summary"],
                    data_source=DataSourceEnum.synthetic,
                )
                session.add(disp)
                total_disputes += 1

                esc_pet = d["petitioner_name"].replace("'", "''")
                esc_resp = d["respondent_name"].replace("'", "''")
                esc_sum = d["summary"].replace("'", "''")
                stay_str = "TRUE" if d["stay_order_active"] else "FALSE"
                sql_batch.append(
                    f"INSERT INTO legal_disputes (id, created_at, updated_at, data_source, project_id, case_number, court_forum, dispute_type, stay_order_active, status, filed_date, delay_impact_estimate_days, petitioner_name, respondent_name, summary) "
                    f"VALUES ('{disp_id}', now(), now(), 'synthetic', '{proj_id}', '{d['case_number']}', '{d['court_forum']}', '{d['dispute_type']}', {stay_str}, '{d['status'].value}', '{d['filed_date']}', {d['delay_impact_estimate_days']}, '{esc_pet}', '{esc_resp}', '{esc_sum}');"
                )

            # Rehabilitation Progress
            r = rec["rehabilitation"]
            rehab_id = uuid.uuid4()
            rehab = RehabilitationProgress(
                id=rehab_id,
                project_id=proj_id,
                total_families_eligible=r["total_families_eligible"],
                families_resettled=r["families_resettled"],
                monetary_allowance_disbursed=r["monetary_allowance_disbursed"],
                alternative_land_allotted_count=r["alternative_land_allotted_count"],
                housing_units_constructed=r["housing_units_constructed"],
                housing_units_allotted=r["housing_units_allotted"],
                rr_scheme_status=r["rr_scheme_status"],
                completion_percentage=r["completion_percentage"],
                notes=r["notes"],
                data_source=DataSourceEnum.synthetic,
            )
            session.add(rehab)
            total_rehabs += 1

            esc_r_notes = r["notes"].replace("'", "''")
            sql_batch.append(
                f"INSERT INTO rehabilitation_progress (id, created_at, updated_at, data_source, project_id, total_families_eligible, families_resettled, monetary_allowance_disbursed, alternative_land_allotted_count, housing_units_constructed, housing_units_allotted, rr_scheme_status, completion_percentage, notes) "
                f"VALUES ('{rehab_id}', now(), now(), 'synthetic', '{proj_id}', {r['total_families_eligible']}, {r['families_resettled']}, {r['monetary_allowance_disbursed']}, {r['alternative_land_allotted_count']}, {r['housing_units_constructed']}, {r['housing_units_allotted']}, '{r['rr_scheme_status'].value}', {r['completion_percentage']}, '{esc_r_notes}');"
            )

            # Stakeholders
            for stk_data in rec["stakeholders"]:
                stk_id = uuid.uuid4()
                stk = Stakeholder(
                    id=stk_id,
                    project_id=proj_id,
                    name=stk_data["name"],
                    role=stk_data["role"],
                    responsiveness_score=stk_data["responsiveness_score"],
                    last_contact_date=stk_data["last_contact_date"],
                    notes=stk_data["notes"],
                    data_source=DataSourceEnum.synthetic,
                )
                session.add(stk)
                total_stks += 1

                esc_stk_name = stk_data["name"].replace("'", "''")
                esc_stk_notes = stk_data["notes"].replace("'", "''")
                sql_batch.append(
                    f"INSERT INTO stakeholders (id, created_at, updated_at, data_source, project_id, name, role, responsiveness_score, last_contact_date, notes) "
                    f"VALUES ('{stk_id}', now(), now(), 'synthetic', '{proj_id}', '{esc_stk_name}', '{stk_data['role']}', {stk_data['responsiveness_score']}, '{stk_data['last_contact_date']}', '{esc_stk_notes}');"
                )

            # Risk Score
            rs = rec["risk_score"]
            risk_id = uuid.uuid4()
            risk_score = RiskScore(
                id=risk_id,
                project_id=proj_id,
                risk_category=rs["risk_category"],
                overall_delay_probability=rs["overall_delay_probability"],
                stage_delay_probabilities=rs["stage_delay_probabilities"],
                predicted_delay_days=rs["predicted_delay_days"],
                confidence_score=rs["confidence_score"],
                top_risk_drivers=rs["top_risk_drivers"],
                computed_at=rs["computed_at"],
                data_source=DataSourceEnum.synthetic,
            )
            session.add(risk_score)
            total_risks += 1

            stage_probs_json = json.dumps(rs["stage_delay_probabilities"]).replace("'", "''")
            top_drivers_json = json.dumps(rs["top_risk_drivers"]).replace("'", "''")
            sql_batch.append(
                f"INSERT INTO risk_scores (id, created_at, updated_at, data_source, project_id, risk_category, overall_delay_probability, stage_delay_probabilities, predicted_delay_days, confidence_score, top_risk_drivers, computed_at) "
                f"VALUES ('{risk_id}', now(), now(), 'synthetic', '{proj_id}', '{rs['risk_category'].value}', {rs['overall_delay_probability']}, '{stage_probs_json}'::jsonb, {rs['predicted_delay_days']}, {rs['confidence_score']}, '{top_drivers_json}'::jsonb, '{rs['computed_at']}');"
            )

            delay_days_list.append(rec["total_delay_days"])
            risk_categories_list.append(rec["risk_category"].value)

        # Commit current batch to SQLAlchemy session
        if not dry_run:
            session.commit()
            sql_batch.append("COMMIT;")
            full_sql = "\n".join(sql_batch)
            proc = subprocess.run(
                ["docker", "exec", "-i", "landsight-postgis", "psql", "-U", "landsight_admin", "-d", "landsight_ai"],
                input=full_sql,
                text=True,
                capture_output=True,
            )
            if proc.returncode == 0:
                print(f"[+] Committed batch {b_start // batch_size + 1} and synced to Docker container.")
            else:
                print(f"[+] Committed batch to database. (Docker notice: {proc.stderr[:100] if proc.stderr else 'ok'})")

    session.close()

    # ---------------------------------------------------------------------------
    # Summary & Distribution Sanity Check
    # ---------------------------------------------------------------------------
    print("\n=======================================================")
    print(" SUMMARY: Total Records Staged & Inserted")
    print("=======================================================")
    print(f"  projects:                 {total_projects}")
    print(f"  stages:                   {total_stages} (5 per project)")
    print(f"  compensation_records:     {total_comps}")
    print(f"  legal_disputes:           {total_disputes} (~{total_disputes * 100 / total_projects:.1f}%)")
    print(f"  rehabilitation_progress:  {total_rehabs}")
    print(f"  stakeholders:             {total_stks} (~{total_stks / total_projects:.2f} per project)")
    print(f"  risk_scores:              {total_risks}")
    print("=======================================================\n")

    print_distribution_sanity_check(delay_days_list, risk_categories_list)


def print_distribution_sanity_check(delays: list, categories: list):
    """Prints ASCII histogram and quartile statistics verifying non-uniform realistic distribution."""
    delays_arr = np.array(delays)
    n = len(delays_arr)

    print("=======================================================")
    print(" SANITY CHECK: Delay Days & Risk Category Distribution")
    print("=======================================================")

    p25, p50, p75, p90, p99 = np.percentile(delays_arr, [25, 50, 75, 90, 99])
    mean_delay = float(np.mean(delays_arr))
    std_delay = float(np.std(delays_arr))

    print(f"  Mean Delay:     {mean_delay:.1f} days")
    print(f"  Median Delay:   {p50:.1f} days")
    print(f"  Std Deviation:  {std_delay:.1f} days")
    print(f"  Min / Max:      {np.min(delays_arr)} / {np.max(delays_arr)} days")
    print(f"  Quartiles:      P25={p25:.1f}d | P50={p50:.1f}d | P75={p75:.1f}d | P90={p90:.1f}d | P99={p99:.1f}d")
    print("-" * 55)

    # Risk Category Distribution
    cat_counts = Counter(categories)
    print("\n  Risk Category Breakdown (Target: Low ~35%, Med ~30%, High ~20%, Critical ~15%):")
    for cat in ["low", "medium", "high", "critical"]:
        cnt = cat_counts.get(cat, 0)
        pct = (cnt / n) * 100
        bar = "#" * int(pct / 2)
        print(f"    {cat:<9} | {cnt:>5} ({pct:>5.1f}%) | {bar}")

    # Delay Days Histogram Bins
    bins = [(0, 35), (36, 95), (96, 180), (181, 300), (301, 500), (501, 750)]
    print("\n  Delay Days Histogram Breakdown:")
    for b_low, b_high in bins:
        count_in_bin = int(np.sum((delays_arr >= b_low) & (delays_arr <= b_high)))
        pct = (count_in_bin / n) * 100
        bar = "=" * int(pct / 2)
        print(f"    {b_low:>3} - {b_high:>4} d | {count_in_bin:>5} ({pct:>5.1f}%) | {bar}")

    print("=======================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LandSight AI - Synthetic Dataset Generation Engine")
    parser.add_argument("--count", type=int, default=3500, help="Number of projects to generate (default: 3500)")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch commit size (default: 500)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate generation without committing changes")
    args = parser.parse_args()

    generate_and_insert(
        count=args.count,
        batch_size=args.batch_size,
        seed=args.seed,
        dry_run=args.dry_run,
    )
