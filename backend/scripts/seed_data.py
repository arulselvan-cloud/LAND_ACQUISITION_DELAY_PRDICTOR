"""LandSight AI - Database Seed Script.

Populates initial benchmark projects, 5 lifecycle statutory stages, compensation records,
legal disputes, rehabilitation progress, ML risk scores with per-stage delay distributions,
prescriptive recommendations, early warning alerts, and key stakeholders.

Usage:
    python backend/scripts/seed_data.py [--dry-run]
"""

import argparse
import datetime
import sys
from pathlib import Path
from geoalchemy2.elements import WKTElement

# Add project root and backend to sys.path
backend_dir = Path(__file__).resolve().parents[1]
root_dir = backend_dir.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(backend_dir))

from backend.app.database import Base, SessionLocal, engine
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


def get_seed_payloads():
    """Generates 3 realistic Indian infrastructure land acquisition project datasets."""
    today = datetime.date.today()

    return [
        {
            "project": {
                "name": "Chennai-Bengaluru Industrial Corridor (CBIC) - Package 2",
                "project_code": "CBIC-TN-PKG02",
                "district": "Ranipet",
                "state": "Tamil Nadu",
                "project_type": "Industrial / Expressway",
                "land_area_hectares": 340.5,
                "affected_families_count": 420,
                "notification_date": today - datetime.timedelta(days=480),
                "target_possession_date": today + datetime.timedelta(days=120),
                "status": "delayed",
                "location": WKTElement("POINT(79.3326 12.9298)", srid=4326),
                "data_source": DataSourceEnum.real,
            },
            "stages": [
                {
                    "stage_name": StageNameEnum.notification,
                    "stage_order": 1,
                    "planned_duration_days": 60,
                    "actual_duration_days": 65,
                    "status": StageStatusEnum.completed,
                    "start_date": today - datetime.timedelta(days=480),
                    "actual_completion_date": today - datetime.timedelta(days=415),
                    "delay_days": 5,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "stage_name": StageNameEnum.survey,
                    "stage_order": 2,
                    "planned_duration_days": 90,
                    "actual_duration_days": 130,
                    "status": StageStatusEnum.completed,
                    "start_date": today - datetime.timedelta(days=415),
                    "actual_completion_date": today - datetime.timedelta(days=285),
                    "delay_days": 40,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "stage_name": StageNameEnum.compensation,
                    "stage_order": 3,
                    "planned_duration_days": 120,
                    "actual_duration_days": None,
                    "status": StageStatusEnum.delayed,
                    "start_date": today - datetime.timedelta(days=285),
                    "target_completion_date": today - datetime.timedelta(days=165),
                    "delay_days": 120,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "stage_name": StageNameEnum.possession,
                    "stage_order": 4,
                    "planned_duration_days": 90,
                    "actual_duration_days": None,
                    "status": StageStatusEnum.not_started,
                    "delay_days": 0,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "stage_name": StageNameEnum.rehabilitation,
                    "stage_order": 5,
                    "planned_duration_days": 150,
                    "actual_duration_days": None,
                    "status": StageStatusEnum.in_progress,
                    "start_date": today - datetime.timedelta(days=200),
                    "delay_days": 45,
                    "data_source": DataSourceEnum.real,
                },
            ],
            "compensation": {
                "total_amount_allocated": 145000000.00,  # 14.5 Crore INR
                "total_amount_disbursed": 87000000.00,   # 8.7 Crore INR
                "beneficiaries_count": 420,
                "disbursed_count": 252,
                "valuation_method": "RFCTLARR 2013: Guideline Value x 1.5 Multiplier + 100% Solatium",
                "status": CompensationStatusEnum.partially_disbursed,
                "last_disbursement_date": today - datetime.timedelta(days=14),
                "notes": "Valuation disputes raised by 3 farmer cooperatives in Arakkonam taluk.",
                "data_source": DataSourceEnum.real,
            },
            "disputes": [
                {
                    "case_number": "WP/MD/2491/2023",
                    "court_forum": "Madras High Court",
                    "dispute_type": "Valuation and Multiplier Conflict",
                    "stay_order_active": True,
                    "status": DisputeStatusEnum.stay_granted,
                    "filed_date": today - datetime.timedelta(days=180),
                    "delay_impact_estimate_days": 90,
                    "petitioner_name": "Ranipet Land Owners Welfare Association",
                    "respondent_name": "District Revenue Officer & Competent Authority (L.A.)",
                    "summary": "Interim stay granted on 18.4 hectares pending re-determination of market factor multiplier.",
                    "data_source": DataSourceEnum.real,
                }
            ],
            "rehabilitation": {
                "total_families_eligible": 180,
                "families_resettled": 95,
                "monetary_allowance_disbursed": 19000000.00,
                "alternative_land_allotted_count": 60,
                "housing_units_constructed": 110,
                "housing_units_allotted": 90,
                "rr_scheme_status": RRSchemeStatusEnum.in_progress,
                "completion_percentage": 52.8,
                "notes": "R&R township basic infrastructure works 75% complete.",
                "data_source": DataSourceEnum.real,
            },
            "risk_score": {
                "risk_category": RiskCategoryEnum.critical,
                "overall_delay_probability": 0.84,
                "stage_delay_probabilities": {
                    "notification": 0.05,
                    "survey": 0.32,
                    "compensation": 0.88,
                    "possession": 0.85,
                    "rehabilitation": 0.62,
                },
                "predicted_delay_days": 145,
                "confidence_score": 0.92,
                "top_risk_drivers": [
                    {"factor": "stay_order_active", "impact": 0.42, "description": "High Court interim stay halting possession"},
                    {"factor": "compensation_disbursement_gap", "impact": 0.28, "description": "40% allocated compensation undisbursed"},
                    {"factor": "rr_housing_delay", "impact": 0.14, "description": "48% eligible families pending resettlement"},
                ],
                "data_source": DataSourceEnum.real,
            },
            "recommendations": [
                {
                    "action_text": "Convene Special Revenue Lok Adalat to negotiate solatium enhancement for Arakkonam taluk litigating farmers.",
                    "priority": PriorityEnum.urgent,
                    "category": "Legal / Valuation",
                    "expected_impact": "Resolves High Court stay order; saves estimated 75 days of possession delay.",
                    "is_implemented": False,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "action_text": "Fast-track R&R township electrical substation commissioning to enable immediate possession handover.",
                    "priority": PriorityEnum.high,
                    "category": "Rehabilitation",
                    "expected_impact": "Accelerates 45 family relocations within 30 days.",
                    "is_implemented": False,
                    "data_source": DataSourceEnum.real,
                },
            ],
            "alerts": [
                {
                    "title": "Active High Court Stay Order Halting Milestone",
                    "message": "Madras High Court stay in WP/MD/2491/2023 directly blocks possession handover for Package 2.",
                    "severity": AlertSeverityEnum.critical,
                    "resolved": False,
                    "data_source": DataSourceEnum.real,
                }
            ],
            "stakeholders": [
                {
                    "name": "Thiru S. Valarmathi, IAS",
                    "role": "District Collector",
                    "responsiveness_score": 78.5,
                    "last_contact_date": today - datetime.timedelta(days=5),
                    "notes": "Chaired monthly inter-departmental review; requested expedited tribunal submission.",
                    "data_source": DataSourceEnum.real,
                },
                {
                    "name": "K. Ramanathan",
                    "role": "Special Land Acquisition Officer (SLAO)",
                    "responsiveness_score": 62.0,
                    "last_contact_date": today - datetime.timedelta(days=12),
                    "notes": "Understaffed office; requires additional revenue surveyors.",
                    "data_source": DataSourceEnum.real,
                },
                {
                    "name": "NHAI Project Implementation Unit (PIU)",
                    "role": "Project Implementing Agency",
                    "responsiveness_score": 91.0,
                    "last_contact_date": today - datetime.timedelta(days=2),
                    "notes": "Escalated timeline bottleneck to Ministry of Road Transport & Highways.",
                    "data_source": DataSourceEnum.real,
                },
            ],
        },
        {
            "project": {
                "name": "Bengaluru Suburban Rail Project (BSRP) - Corridor 4 (Heelalige to Rajanukunte)",
                "project_code": "BSRP-KA-CORR04",
                "district": "Bengaluru Urban",
                "state": "Karnataka",
                "project_type": "Rail Transit",
                "land_area_hectares": 128.0,
                "affected_families_count": 210,
                "notification_date": today - datetime.timedelta(days=320),
                "target_possession_date": today + datetime.timedelta(days=180),
                "status": "in_progress",
                "location": WKTElement("POINT(77.5946 12.9716)", srid=4326),
                "data_source": DataSourceEnum.real,
            },
            "stages": [
                {
                    "stage_name": StageNameEnum.notification,
                    "stage_order": 1,
                    "planned_duration_days": 45,
                    "actual_duration_days": 42,
                    "status": StageStatusEnum.completed,
                    "start_date": today - datetime.timedelta(days=320),
                    "actual_completion_date": today - datetime.timedelta(days=278),
                    "delay_days": 0,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "stage_name": StageNameEnum.survey,
                    "stage_order": 2,
                    "planned_duration_days": 60,
                    "actual_duration_days": 75,
                    "status": StageStatusEnum.completed,
                    "start_date": today - datetime.timedelta(days=278),
                    "actual_completion_date": today - datetime.timedelta(days=203),
                    "delay_days": 15,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "stage_name": StageNameEnum.compensation,
                    "stage_order": 3,
                    "planned_duration_days": 90,
                    "actual_duration_days": 95,
                    "status": StageStatusEnum.completed,
                    "start_date": today - datetime.timedelta(days=203),
                    "actual_completion_date": today - datetime.timedelta(days=108),
                    "delay_days": 5,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "stage_name": StageNameEnum.possession,
                    "stage_order": 4,
                    "planned_duration_days": 90,
                    "actual_duration_days": None,
                    "status": StageStatusEnum.in_progress,
                    "start_date": today - datetime.timedelta(days=108),
                    "target_completion_date": today - datetime.timedelta(days=18),
                    "delay_days": 20,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "stage_name": StageNameEnum.rehabilitation,
                    "stage_order": 5,
                    "planned_duration_days": 120,
                    "actual_duration_days": None,
                    "status": StageStatusEnum.in_progress,
                    "start_date": today - datetime.timedelta(days=150),
                    "delay_days": 10,
                    "data_source": DataSourceEnum.real,
                },
            ],
            "compensation": {
                "total_amount_allocated": 98000000.00,
                "total_amount_disbursed": 92500000.00,
                "beneficiaries_count": 210,
                "disbursed_count": 198,
                "valuation_method": "KIADB Act Direct Purchase Agreement Formula",
                "status": CompensationStatusEnum.fully_disbursed,
                "last_disbursement_date": today - datetime.timedelta(days=30),
                "notes": "Direct consent agreements executed for 94% of land parcels.",
                "data_source": DataSourceEnum.real,
            },
            "disputes": [
                {
                    "case_number": "OS/771/2024",
                    "court_forum": "City Civil Court Bengaluru",
                    "dispute_type": "Ancestral Partition Title Claim",
                    "stay_order_active": False,
                    "status": DisputeStatusEnum.hearing_scheduled,
                    "filed_date": today - datetime.timedelta(days=90),
                    "delay_impact_estimate_days": 20,
                    "petitioner_name": "Muniswamappa & Sons",
                    "respondent_name": "K-RIDE & Special Deputy Commissioner",
                    "summary": "Private title contestation; compensation deposit deposited into court registry.",
                    "data_source": DataSourceEnum.real,
                }
            ],
            "rehabilitation": {
                "total_families_eligible": 65,
                "families_resettled": 58,
                "monetary_allowance_disbursed": 8500000.00,
                "alternative_land_allotted_count": 0,
                "housing_units_constructed": 65,
                "housing_units_allotted": 58,
                "rr_scheme_status": RRSchemeStatusEnum.in_progress,
                "completion_percentage": 89.2,
                "notes": "Final 7 commercial tenants scheduled for relocation next week.",
                "data_source": DataSourceEnum.real,
            },
            "risk_score": {
                "risk_category": RiskCategoryEnum.low,
                "overall_delay_probability": 0.22,
                "stage_delay_probabilities": {
                    "notification": 0.02,
                    "survey": 0.15,
                    "compensation": 0.12,
                    "possession": 0.28,
                    "rehabilitation": 0.18,
                },
                "predicted_delay_days": 18,
                "confidence_score": 0.89,
                "top_risk_drivers": [
                    {"factor": "commercial_tenant_relocation", "impact": 0.15, "description": "7 urban commercial tenants pending final key handover"},
                    {"factor": "utility_shifting", "impact": 0.08, "description": "BESCOM powerline relocation co-ordination"},
                ],
                "data_source": DataSourceEnum.real,
            },
            "recommendations": [
                {
                    "action_text": "Coordinate joint site inspection with BESCOM for transmission pole relocation along Corridor 4.",
                    "priority": PriorityEnum.medium,
                    "category": "Administrative / Utilities",
                    "expected_impact": "Unlocks final 1.2 km right of way on schedule.",
                    "is_implemented": True,
                    "data_source": DataSourceEnum.real,
                }
            ],
            "alerts": [
                {
                    "title": "Minor Utility Shifting Delay Alert",
                    "message": "BESCOM utility relocation lagging by 10 days; low risk to critical track-laying path.",
                    "severity": AlertSeverityEnum.low,
                    "resolved": False,
                    "data_source": DataSourceEnum.real,
                }
            ],
            "stakeholders": [
                {
                    "name": "Special Deputy Commissioner (Land Acquisition)",
                    "role": "Competent Authority",
                    "responsiveness_score": 88.0,
                    "last_contact_date": today - datetime.timedelta(days=3),
                    "notes": "Fast-tracked consent award disbursement under KIADB Section 29(2).",
                    "data_source": DataSourceEnum.real,
                },
                {
                    "name": "K-RIDE Chief General Manager (Civil)",
                    "role": "Project Implementing Agency",
                    "responsiveness_score": 94.0,
                    "last_contact_date": today - datetime.timedelta(days=1),
                    "notes": "Proactive weekly tracking meetings with municipal agencies.",
                    "data_source": DataSourceEnum.real,
                },
            ],
        },
        {
            "project": {
                "name": "Mumbai-Ahmedabad High Speed Rail (MAHSR) - Palghar Section",
                "project_code": "MAHSR-MH-PAL03",
                "district": "Palghar",
                "state": "Maharashtra",
                "project_type": "High Speed Rail",
                "land_area_hectares": 286.4,
                "affected_families_count": 890,
                "notification_date": today - datetime.timedelta(days=600),
                "target_possession_date": today + datetime.timedelta(days=60),
                "status": "delayed",
                "location": WKTElement("POINT(72.7689 19.6967)", srid=4326),
                "data_source": DataSourceEnum.real,
            },
            "stages": [
                {
                    "stage_name": StageNameEnum.notification,
                    "stage_order": 1,
                    "planned_duration_days": 60,
                    "actual_duration_days": 90,
                    "status": StageStatusEnum.completed,
                    "start_date": today - datetime.timedelta(days=600),
                    "actual_completion_date": today - datetime.timedelta(days=510),
                    "delay_days": 30,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "stage_name": StageNameEnum.survey,
                    "stage_order": 2,
                    "planned_duration_days": 90,
                    "actual_duration_days": 180,
                    "status": StageStatusEnum.completed,
                    "start_date": today - datetime.timedelta(days=510),
                    "actual_completion_date": today - datetime.timedelta(days=330),
                    "delay_days": 90,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "stage_name": StageNameEnum.compensation,
                    "stage_order": 3,
                    "planned_duration_days": 120,
                    "actual_duration_days": None,
                    "status": StageStatusEnum.delayed,
                    "start_date": today - datetime.timedelta(days=330),
                    "delay_days": 150,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "stage_name": StageNameEnum.possession,
                    "stage_order": 4,
                    "planned_duration_days": 90,
                    "actual_duration_days": None,
                    "status": StageStatusEnum.delayed,
                    "delay_days": 120,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "stage_name": StageNameEnum.rehabilitation,
                    "stage_order": 5,
                    "planned_duration_days": 180,
                    "actual_duration_days": None,
                    "status": StageStatusEnum.in_progress,
                    "start_date": today - datetime.timedelta(days=250),
                    "delay_days": 90,
                    "data_source": DataSourceEnum.real,
                },
            ],
            "compensation": {
                "total_amount_allocated": 280000000.00,
                "total_amount_disbursed": 175000000.00,
                "beneficiaries_count": 890,
                "disbursed_count": 510,
                "valuation_method": "Multiplied Market Rate + 100% Solatium + 25% Direct Consent Bonus",
                "status": CompensationStatusEnum.partially_disbursed,
                "last_disbursement_date": today - datetime.timedelta(days=8),
                "notes": "Gram Sabha consent pending in 4 tribal villages under PESA Act.",
                "data_source": DataSourceEnum.real,
            },
            "disputes": [
                {
                    "case_number": "PIL/42/2023",
                    "court_forum": "Bombay High Court",
                    "dispute_type": "Tribal Land Rights & PESA Compliance",
                    "stay_order_active": True,
                    "status": DisputeStatusEnum.stay_granted,
                    "filed_date": today - datetime.timedelta(days=220),
                    "delay_impact_estimate_days": 180,
                    "petitioner_name": "Adivasi Ekta Parishad",
                    "respondent_name": "NHSRCL & State of Maharashtra",
                    "summary": "Stay order on possession transfer pending environmental and Gram Sabha consensus documentation.",
                    "data_source": DataSourceEnum.real,
                }
            ],
            "rehabilitation": {
                "total_families_eligible": 450,
                "families_resettled": 210,
                "monetary_allowance_disbursed": 38000000.00,
                "alternative_land_allotted_count": 80,
                "housing_units_constructed": 260,
                "housing_units_allotted": 210,
                "rr_scheme_status": RRSchemeStatusEnum.in_progress,
                "completion_percentage": 46.7,
                "notes": "Community hall and primary health center under construction at resettlement colony.",
                "data_source": DataSourceEnum.real,
            },
            "risk_score": {
                "risk_category": RiskCategoryEnum.critical,
                "overall_delay_probability": 0.91,
                "stage_delay_probabilities": {
                    "notification": 0.10,
                    "survey": 0.45,
                    "compensation": 0.89,
                    "possession": 0.94,
                    "rehabilitation": 0.78,
                },
                "predicted_delay_days": 210,
                "confidence_score": 0.94,
                "top_risk_drivers": [
                    {"factor": "tribal_pesa_clearance", "impact": 0.45, "description": "Mandatory Gram Sabha consent resolution pending in 4 villages"},
                    {"factor": "stay_order_active", "impact": 0.35, "description": "Bombay High Court stay in PIL/42/2023"},
                    {"factor": "low_stakeholder_responsiveness", "impact": 0.12, "description": "Local Panchayat authority responsiveness scored below 45"},
                ],
                "data_source": DataSourceEnum.real,
            },
            "recommendations": [
                {
                    "action_text": "Engage designated Tribal Advisory Council and local community elders for structured dialogue on PESA consent.",
                    "priority": PriorityEnum.urgent,
                    "category": "Stakeholder / Policy",
                    "expected_impact": "Resolves Gram Sabha deadlock; mitigates 110 days of forecasted litigation delay.",
                    "is_implemented": False,
                    "data_source": DataSourceEnum.real,
                },
                {
                    "action_text": "Deploy mobile banking camps for instant on-the-spot DBT disbursement to consent-awarded farmers.",
                    "priority": PriorityEnum.high,
                    "category": "Compensation",
                    "expected_impact": "Increases compensation disbursement rate by 25% within 3 weeks.",
                    "is_implemented": False,
                    "data_source": DataSourceEnum.real,
                },
            ],
            "alerts": [
                {
                    "title": "Critical Statutory Milestone Breach: Gram Sabha Consensus Pending",
                    "message": "PESA Act Section 4(i) consultation deadline lapsed for Palghar package.",
                    "severity": AlertSeverityEnum.critical,
                    "resolved": False,
                    "data_source": DataSourceEnum.real,
                }
            ],
            "stakeholders": [
                {
                    "name": "Govind Bodke, IAS",
                    "role": "District Collector",
                    "responsiveness_score": 72.0,
                    "last_contact_date": today - datetime.timedelta(days=7),
                    "notes": "Convening tribal welfare sub-committee next Monday.",
                    "data_source": DataSourceEnum.real,
                },
                {
                    "name": "Palghar Gram Sabha Federation",
                    "role": "Gram Panchayat / Local Body",
                    "responsiveness_score": 42.0,
                    "last_contact_date": today - datetime.timedelta(days=21),
                    "notes": "Low responsiveness; demands revision of compensation packages for forest dwelling communities.",
                    "data_source": DataSourceEnum.real,
                },
                {
                    "name": "NHSRCL Chief Project Manager",
                    "role": "Project Implementing Agency",
                    "responsiveness_score": 88.0,
                    "last_contact_date": today - datetime.timedelta(days=2),
                    "notes": "Submitted enhanced rehabilitation township plan for administrative sanction.",
                    "data_source": DataSourceEnum.real,
                },
            ],
        },
    ]


def seed_database(dry_run: bool = False):
    """Executes database seeding with transaction safety."""
    print(f"[*] Beginning LandSight AI database seed routine (dry_run={dry_run})...")

    payloads = get_seed_payloads()
    session = SessionLocal()

    try:
        total_projects = 0
        total_stages = 0
        total_disputes = 0
        total_rehab = 0
        total_risks = 0
        total_recs = 0
        total_alerts = 0
        total_stakeholders = 0

        for item in payloads:
            proj_data = item["project"]
            # Check for existing project code
            existing = session.query(Project).filter(Project.project_code == proj_data["project_code"]).first()
            if existing:
                print(f"[-] Project '{proj_data['project_code']}' already exists. Skipping insertion.")
                continue

            # 1. Create Project
            project = Project(**proj_data)
            session.add(project)
            session.flush()  # assign project.id
            total_projects += 1

            # 2. Create Stages (5 lifecycle stages)
            for stage_data in item["stages"]:
                stage = Stage(project_id=project.id, **stage_data)
                session.add(stage)
                total_stages += 1

            # 3. Create Compensation Record
            comp_data = item.get("compensation")
            if comp_data:
                comp = CompensationRecord(project_id=project.id, **comp_data)
                session.add(comp)

            # 4. Create Legal Disputes
            for disp_data in item.get("disputes", []):
                disp = LegalDispute(project_id=project.id, **disp_data)
                session.add(disp)
                total_disputes += 1

            # 5. Create Rehabilitation Progress
            rehab_data = item.get("rehabilitation")
            if rehab_data:
                rehab = RehabilitationProgress(project_id=project.id, **rehab_data)
                session.add(rehab)
                total_rehab += 1

            # 6. Create Risk Score
            risk_data = item.get("risk_score")
            risk_score = None
            if risk_data:
                risk_score = RiskScore(project_id=project.id, **risk_data)
                session.add(risk_score)
                session.flush()  # assign risk_score.id
                total_risks += 1

            # 7. Create Recommendations
            for rec_data in item.get("recommendations", []):
                rec = Recommendation(
                    project_id=project.id,
                    risk_score_id=risk_score.id if risk_score else None,
                    **rec_data,
                )
                session.add(rec)
                total_recs += 1

            # 8. Create Alerts
            for alert_data in item.get("alerts", []):
                alert = Alert(project_id=project.id, **alert_data)
                session.add(alert)
                total_alerts += 1

            # 9. Create Stakeholders
            for stk_data in item.get("stakeholders", []):
                stk = Stakeholder(project_id=project.id, **stk_data)
                session.add(stk)
                total_stakeholders += 1

            print(f"[+] Staged project: {project.name} ({project.project_code})")

        if dry_run:
            print("[*] Dry run mode enabled. Rolling back transaction without changes.")
            session.rollback()
        else:
            session.commit()
            print("[*] Transaction committed successfully to database.")

        print("\n--- Seed Summary ---")
        print(f"Projects seeded:     {total_projects}")
        print(f"Stages seeded:       {total_stages}")
        print(f"Legal disputes:      {total_disputes}")
        print(f"R&R progress rows:   {total_rehab}")
        print(f"Risk score models:   {total_risks}")
        print(f"Recommendations:     {total_recs}")
        print(f"Early-warning alerts:{total_alerts}")
        print(f"Stakeholders:        {total_stakeholders}")
        print("--------------------\n")

    except Exception as exc:
        session.rollback()
        print(f"[!] Seed execution encountered error: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed initial LandSight AI database.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without committing changes")
    args = parser.parse_args()

    seed_database(dry_run=args.dry_run)
