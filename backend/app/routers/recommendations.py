"""LandSight AI - AI Recommendations & Executive Action Plan Router.

Provides endpoints to trigger real-time AI recommendation synthesis using Gemini 2.5 Flash
grounded in SHAP explainability drivers, persist action directives and alerts, and retrieve stored recommendations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.alert import Alert
from backend.app.models.enums import AlertSeverityEnum, PriorityEnum
from backend.app.models.notification import NotificationLog
from backend.app.models.project import Project
from backend.app.models.recommendation import Recommendation
from backend.app.models.risk import RiskScore
from backend.app.services.llm_recommendations import generate_action_memo
from backend.app.services.project_lookup import get_project_or_404
from backend.app.services.recommendation_engine import get_rule_based_recommendations
from ml.explain import ModelExplainer

router = APIRouter()


class NotificationLogItem(BaseModel):
    id: str
    alert_id: str
    channel: str
    recipient_role: str
    message: str
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationItem(BaseModel):
    id: str
    action_text: str
    priority: str
    category: Optional[str] = None
    expected_impact: Optional[str] = None
    is_implemented: bool = False
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GenerateRecommendationResponse(BaseModel):
    project_id: str
    project_code: str
    name: str
    predicted_risk_category: str
    delay_probability: float
    memo: str
    is_llm_generated: bool
    fallback_used: bool
    model: str
    recommendations: List[RecommendationItem]
    alert_created: bool
    notification_dispatched: bool = False
    notification_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectRecommendationsListResponse(BaseModel):
    project_id: str
    project_code: str
    total_recommendations: int
    recommendations: List[RecommendationItem]

    model_config = ConfigDict(from_attributes=True)


@router.post(
    "/projects/{project_id}/generate-recommendation",
    response_model=GenerateRecommendationResponse,
    tags=["AI Recommendations & Alerts"],
)
def generate_project_recommendation(
    project_id: str,
    request: Request,
    simulate_failure: bool = Query(
        False,
        description="Simulate LLM failure to exercise deterministic fallback path",
    ),
    db: Session = Depends(get_db),
):
    """Generates an executive administrative action memo and detailed statutory directives.

    Uses Gemini 2.5 Flash grounded in SHAP explainability. Automatically persists recommendations
    to the database and triggers an early warning alert if project is High or Critical risk.
    """
    proj = get_project_or_404(db, project_id)
    canonical_id = str(proj.id)

    # 1. Obtain explanation
    classifier_bundle = getattr(request.app.state, "risk_classifier", None)
    tree_explainer = getattr(request.app.state, "tree_explainer", None)
    explainer = ModelExplainer(bundle=classifier_bundle, explainer=tree_explainer)
    explanation = explainer.explain_prediction(canonical_id, session=db)

    pred_cat = explanation.get("predicted_risk_category", "medium")
    probs = explanation.get("prediction_probabilities", {})
    delay_prob = round(float(probs.get("high", 0.0) + probs.get("critical", 0.0)), 4)

    # 2. Rule-based recommendations
    rule_recs = get_rule_based_recommendations(
        canonical_id, explanation=explanation, session=db, explainer=explainer
    )

    # 3. Generate LLM memo (with fallback)
    memo_result = generate_action_memo(
        proj, explanation, rule_recs, simulate_failure=simulate_failure
    )

    # 4. Find latest risk score
    latest_risk = (
        db.query(RiskScore)
        .filter(RiskScore.project_id == proj.id)
        .order_by(RiskScore.computed_at.desc())
        .first()
    )

    # 5. Persist Executive Directive Memo (upsert to avoid duplicates upon repeated clicks)
    memo_priority = (
        PriorityEnum.urgent
        if pred_cat == "critical"
        else (PriorityEnum.high if pred_cat == "high" else PriorityEnum.medium)
    )

    existing_exec = (
        db.query(Recommendation)
        .filter(
            Recommendation.project_id == proj.id,
            Recommendation.category == "Executive Directive",
        )
        .order_by(Recommendation.created_at.desc())
        .first()
    )

    if existing_exec:
        existing_exec.action_text = memo_result["memo"]
        existing_exec.priority = memo_priority
        existing_exec.risk_score_id = latest_risk.id if latest_risk else None
        existing_exec.is_implemented = False
        exec_rec = existing_exec
        # Purge any redundant duplicate Executive Directives for this project
        (
            db.query(Recommendation)
            .filter(
                Recommendation.project_id == proj.id,
                Recommendation.category == "Executive Directive",
                Recommendation.id != existing_exec.id,
            )
            .delete(synchronize_session=False)
        )
    else:
        exec_rec = Recommendation(
            project_id=proj.id,
            risk_score_id=latest_risk.id if latest_risk else None,
            action_text=memo_result["memo"],
            priority=memo_priority,
            category="Executive Directive",
            expected_impact="Mitigate statutory milestone delays and unblock inter-agency execution under RFCTLARR 2013",
            is_implemented=False,
            data_source=proj.data_source,
        )
        db.add(exec_rec)
        db.flush()

    # 6. Persist Rule-Based Directives if not already present
    persisted_recs = [exec_rec]
    for r in rule_recs:
        existing = (
            db.query(Recommendation)
            .filter(
                Recommendation.project_id == proj.id,
                Recommendation.action_text == r["action_text"],
            )
            .first()
        )
        if not existing:
            sub_rec = Recommendation(
                project_id=proj.id,
                risk_score_id=latest_risk.id if latest_risk else None,
                action_text=r["action_text"],
                priority=r["priority"],
                category=r["category"],
                expected_impact=r["expected_impact"],
                is_implemented=False,
                data_source=proj.data_source,
            )
            db.add(sub_rec)
            persisted_recs.append(sub_rec)
        else:
            persisted_recs.append(existing)

    # 7. Automatic Alert Trigger & De-duplicated Notification Dispatch
    alert_created = False
    notification_dispatched = False
    notif_msg = None

    if pred_cat in ["high", "critical"]:
        target_severity = (
            AlertSeverityEnum.critical
            if pred_cat == "critical"
            else AlertSeverityEnum.high
        )
        existing_alert = (
            db.query(Alert)
            .filter(Alert.project_id == proj.id, Alert.resolved == False)
            .first()
        )

        should_dispatch_notification = False
        target_alert = None

        if not existing_alert:
            new_alert = Alert(
                project_id=proj.id,
                title=f"{proj.project_code}: Priority Delay Bottleneck Alert",
                message=memo_result["memo"][:240] + "...",
                severity=target_severity,
                resolved=False,
                data_source=proj.data_source,
            )
            db.add(new_alert)
            db.flush()
            alert_created = True
            target_alert = new_alert
            # Case (a): Brand-new alert created -> Dispatch initial notification
            should_dispatch_notification = True
        else:
            previous_severity = existing_alert.severity
            severity_changed = (previous_severity != target_severity)
            existing_alert.message = memo_result["memo"][:240] + "..."
            existing_alert.severity = target_severity
            target_alert = existing_alert

            # Check if alert has any prior notification
            has_prior_notification = (
                db.query(NotificationLog)
                .filter(NotificationLog.alert_id == existing_alert.id)
                .first() is not None
            )

            # Case (b): Existing alert severity changed (e.g. HIGH -> CRITICAL) or backfill un-notified alert
            if severity_changed or not has_prior_notification:
                should_dispatch_notification = True
            else:
                # Severity unchanged and notification already logged -> do NOT duplicate
                should_dispatch_notification = False

        if should_dispatch_notification and target_alert:
            # Determine top delay driver from explanation factors
            top_driver = "Statutory milestone delays"
            if explanation.get("factors"):
                risk_factors = [
                    f for f in explanation["factors"] if f.get("direction") == "increases_risk"
                ]
                if risk_factors:
                    top_driver = risk_factors[0].get(
                        "display_name", risk_factors[0].get("feature", "Statutory milestone delays")
                    )
                else:
                    top_driver = explanation["factors"][0].get(
                        "display_name", "Statutory milestone delays"
                    )

            notif_msg = (
                f"LandSight AI Alert: {proj.project_code} flagged {pred_cat.upper()} risk — "
                f"{top_driver}. Immediate review required."
            )

            simulated_notif = NotificationLog(
                alert_id=target_alert.id,
                channel="sms",
                recipient_role="District Collector",
                message=notif_msg,
                data_source=proj.data_source,
            )
            db.add(simulated_notif)
            notification_dispatched = True
        elif target_alert and not should_dispatch_notification:
            # Fetch latest existing notification message for UI feedback
            latest_n = (
                db.query(NotificationLog)
                .filter(NotificationLog.alert_id == target_alert.id)
                .order_by(NotificationLog.sent_at.desc())
                .first()
            )
            if latest_n:
                notif_msg = latest_n.message

    db.commit()

    return GenerateRecommendationResponse(
        project_id=canonical_id,
        project_code=proj.project_code,
        name=proj.name,
        predicted_risk_category=pred_cat,
        delay_probability=delay_prob,
        memo=memo_result["memo"],
        is_llm_generated=memo_result["is_llm_generated"],
        fallback_used=memo_result["fallback_used"],
        model=memo_result["model"],
        recommendations=[
            RecommendationItem(
                id=str(r.id),
                action_text=r.action_text,
                priority=r.priority.value if hasattr(r.priority, "value") else str(r.priority),
                category=r.category,
                expected_impact=r.expected_impact,
                is_implemented=bool(r.is_implemented),
                created_at=r.created_at,
            )
            for r in persisted_recs
        ],
        alert_created=alert_created,
        notification_dispatched=notification_dispatched,
        notification_message=notif_msg,
    )


@router.get(
    "/projects/{project_id}/recommendations",
    response_model=ProjectRecommendationsListResponse,
    tags=["AI Recommendations & Alerts"],
)
def get_project_recommendations(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves all stored administrative recommendations and action directives for a project."""
    proj = get_project_or_404(db, project_id)

    recs = (
        db.query(Recommendation)
        .filter(Recommendation.project_id == proj.id)
        .order_by(Recommendation.created_at.desc())
        .all()
    )

    return ProjectRecommendationsListResponse(
        project_id=str(proj.id),
        project_code=proj.project_code,
        total_recommendations=len(recs),
        recommendations=[
            RecommendationItem(
                id=str(r.id),
                action_text=r.action_text,
                priority=r.priority.value if hasattr(r.priority, "value") else str(r.priority),
                category=r.category,
                expected_impact=r.expected_impact,
                is_implemented=bool(r.is_implemented),
                created_at=r.created_at,
            )
            for r in recs
        ],
    )


@router.get(
    "/alerts/{alert_id}/notifications",
    response_model=List[NotificationLogItem],
    tags=["AI Recommendations & Alerts"],
)
def get_alert_notifications(
    alert_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves simulated notification dispatch logs for an alert (by alert UUID, or project UUID/code)."""
    target_alert_id = None
    try:
        a_uuid = UUID(alert_id)
        alert = db.query(Alert).filter(Alert.id == a_uuid).first()
        if alert:
            target_alert_id = alert.id
    except ValueError:
        pass

    if not target_alert_id:
        try:
            proj = get_project_or_404(db, alert_id)
            latest_alert = (
                db.query(Alert)
                .filter(Alert.project_id == proj.id)
                .order_by(Alert.triggered_at.desc())
                .first()
            )
            if latest_alert:
                target_alert_id = latest_alert.id
        except HTTPException:
            pass

    if not target_alert_id:
        # Check if direct alert_id matches notification_log directly
        try:
            a_uuid = UUID(alert_id)
            notifs = (
                db.query(NotificationLog)
                .filter(NotificationLog.alert_id == a_uuid)
                .order_by(NotificationLog.sent_at.desc())
                .all()
            )
            if notifs:
                return [
                    NotificationLogItem(
                        id=str(n.id),
                        alert_id=str(n.alert_id),
                        channel=n.channel,
                        recipient_role=n.recipient_role,
                        message=n.message,
                        sent_at=n.sent_at,
                    )
                    for n in notifs
                ]
        except ValueError:
            pass

        raise HTTPException(
            status_code=404,
            detail=f"Alert with identifier '{alert_id}' not found.",
        )

    notifs = (
        db.query(NotificationLog)
        .filter(NotificationLog.alert_id == target_alert_id)
        .order_by(NotificationLog.sent_at.desc())
        .all()
    )

    return [
        NotificationLogItem(
            id=str(n.id),
            alert_id=str(n.alert_id),
            channel=n.channel,
            recipient_role=n.recipient_role,
            message=n.message,
            sent_at=n.sent_at,
        )
        for n in notifs
    ]
