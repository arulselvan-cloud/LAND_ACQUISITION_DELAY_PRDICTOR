"""LandSight AI - Predictions & Simulation Router.

Provides real-time machine learning inference, SHAP local explainability,
sequential milestone delay propagation, and interactive what-if counterfactual simulations.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
import numpy as np
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.project_lookup import get_project_or_404
from ml.explain import ModelExplainer
from ml.features import get_project_feature_vector
from ml.propagation import propagate_delay
from ml.what_if import what_if

router = APIRouter()


class PredictionResponse(BaseModel):
    project_id: str
    risk_category: str
    delay_probability: float
    confidence_score: float

    model_config = ConfigDict(from_attributes=True)


class SHAPFactor(BaseModel):
    feature: str
    display_name: str
    value: Optional[Any] = None
    direction: str
    magnitude: float
    shap_value: float


class ExplainResponse(BaseModel):
    project_id: str
    predicted_risk_category: str
    factors: List[SHAPFactor]
    prediction_probabilities: Dict[str, float]


class PropagationStage(BaseModel):
    stage_name: str
    stage_order: int
    status: str
    delay_days: int
    is_predicted: bool


class WhatIfRequest(BaseModel):
    """Pydantic validated hypothetical feature modifications."""
    compensation_disbursed_pct: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Disbursed compensation percentage (0 - 100%)"
    )
    has_active_legal_dispute: Optional[int] = Field(
        None, ge=0, le=1, description="Active court injunction / stay order (0 or 1)"
    )
    dispute_delay_impact_days: Optional[int] = Field(
        None, ge=0, description="Estimated delay impact in days (>= 0)"
    )
    avg_stakeholder_responsiveness: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Stakeholder responsiveness index (0 - 100)"
    )
    rehabilitation_completion_pct: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="R&R completion percentage (0 - 100%)"
    )
    affected_families_count: Optional[int] = Field(
        None, ge=0, description="Number of project-affected families (>= 0)"
    )
    land_area_hectares: Optional[float] = Field(
        None, ge=0.0, description="Total land area in hectares (>= 0)"
    )
    project_type: Optional[str] = Field(
        None, description="Infrastructure sector type"
    )
    state: Optional[str] = Field(
        None, description="State jurisdiction"
    )


@router.post("/predict/{project_id}", response_model=PredictionResponse)
def predict_project_risk(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Extracts project features, executes XGBoost classifier, and returns risk category and delay probability."""
    proj = get_project_or_404(db, project_id)
    canonical_id = str(proj.id)

    # Access preloaded classifier bundle
    classifier_bundle = getattr(request.app.state, "risk_classifier", None)
    if not classifier_bundle:
        raise HTTPException(status_code=500, detail="Risk classifier model is not loaded in application state.")

    model = classifier_bundle["model"]
    encoders = classifier_bundle["encoders"]
    inv_label_map = classifier_bundle["inv_label_map"]

    feat_df = get_project_feature_vector(canonical_id, encoders, session=db)
    probs = model.predict_proba(feat_df)[0]
    pred_idx = int(np.argmax(probs))
    pred_cat = inv_label_map[pred_idx]

    # Delay probability is the cumulative probability of High + Critical risk
    delay_prob = float(probs[2] + probs[3])
    confidence_score = float(np.max(probs))

    return PredictionResponse(
        project_id=canonical_id,
        risk_category=pred_cat,
        delay_probability=round(delay_prob, 4),
        confidence_score=round(confidence_score, 4),
    )


@router.get("/projects/{project_id}/explain", response_model=ExplainResponse)
def explain_project_risk(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Computes SHAP feature attribution and returns the top 5 risk drivers."""
    proj = get_project_or_404(db, project_id)
    canonical_id = str(proj.id)

    classifier_bundle = getattr(request.app.state, "risk_classifier", None)
    tree_explainer = getattr(request.app.state, "tree_explainer", None)
    if not classifier_bundle:
        raise HTTPException(status_code=500, detail="Risk classifier model is not loaded in application state.")

    explainer = ModelExplainer(bundle=classifier_bundle, explainer=tree_explainer)
    explanation = explainer.explain_prediction(canonical_id, session=db)

    top_drivers = [
        SHAPFactor(
            feature=d["feature"],
            display_name=d["display_name"],
            value=d["value"],
            direction=d["direction"],
            magnitude=d["magnitude"],
            shap_value=d["shap_value"],
        )
        for d in explanation["top_drivers"]
    ]

    return ExplainResponse(
        project_id=canonical_id,
        predicted_risk_category=explanation["predicted_risk_category"],
        factors=top_drivers,
        prediction_probabilities=explanation["prediction_probabilities"],
    )


@router.get("/projects/{project_id}/propagation", response_model=List[PropagationStage])
def get_project_delay_propagation(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Computes sequential delay propagation across all 5 statutory RFCTLARR milestones."""
    proj = get_project_or_404(db, project_id)
    canonical_id = str(proj.id)

    propagation_models = getattr(request.app.state, "delay_propagation_models", None)
    if not propagation_models:
        raise HTTPException(status_code=500, detail="Delay propagation models not loaded in application state.")

    results = propagate_delay(canonical_id, models=propagation_models, session=db)

    return [
        PropagationStage(
            stage_name=r["stage_name"],
            stage_order=r["stage_order"],
            status=r.get("current_status", r.get("status")),
            delay_days=r.get("actual_or_predicted_delay_days", r.get("delay_days", 0)),
            is_predicted=r["is_predicted"],
        )
        for r in results
    ]


@router.post("/projects/{project_id}/what-if")
def simulate_counterfactual_interventions(
    project_id: str,
    body: WhatIfRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Simulates hypothetical feature modifications and evaluates risk and milestone duration impact."""
    proj = get_project_or_404(db, project_id)
    canonical_id = str(proj.id)

    # Filter out None fields from request body
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    if not changes:
        raise HTTPException(status_code=422, detail="At least one valid feature intervention must be provided.")

    classifier_bundle = getattr(request.app.state, "risk_classifier", None)
    comp_bundle = getattr(request.app.state, "survival_compensation", None)
    poss_bundle = getattr(request.app.state, "survival_possession", None)

    result = what_if(
        canonical_id,
        changes,
        session=db,
        classifier_bundle=classifier_bundle,
        survival_comp_bundle=comp_bundle,
        survival_poss_bundle=poss_bundle,
    )

    return result
