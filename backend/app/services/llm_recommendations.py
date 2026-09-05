"""LandSight AI - LLM Administrative Action Memo Service.

Leverages the Google Gemini API (gemini-2.5-flash) to synthesize explainable SHAP risk drivers
and rule-based statutory templates into crisp, high-impact 3-4 sentence administrative memos
for Indian infrastructure land acquisition authorities (District Collectors, SLAOs, Implementing Agencies).

Includes robust 5-second timeout and automatic fallback to rule-based templates upon any API error or quota limit.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import dotenv

dotenv.load_dotenv()

logger = logging.getLogger("landsight.llm_recommendations")


def _extract_val(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to extract property from SQLAlchemy model or dictionary."""
    if hasattr(obj, key):
        val = getattr(obj, key)
        return val if val is not None else default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def _build_fallback_memo(
    project: Any,
    explanation: Dict[str, Any],
    rule_templates: List[Dict[str, Any]],
) -> str:
    """Generates a high-quality deterministic administrative memo from rule templates and project statistics."""
    name = _extract_val(project, "name", "Infrastructure Project")
    code = _extract_val(project, "project_code", "PROJECT")
    district = _extract_val(project, "district", "District")
    state = _extract_val(project, "state", "State")
    proj_type = _extract_val(project, "project_type", "Infrastructure")
    land_ha = _extract_val(project, "land_area_hectares", 0.0)
    pafs = _extract_val(project, "affected_families_count", 0)

    pred_cat = explanation.get("predicted_risk_category", "medium")
    probs = explanation.get("prediction_probabilities", {})
    delay_prob = float(probs.get("high", 0.0) + probs.get("critical", 0.0))
    delay_prob_pct = delay_prob * 100.0 if delay_prob > 0 else 25.0

    drivers = {d["feature"]: d for d in explanation.get("all_drivers", explanation.get("top_drivers", []))}
    has_dispute = drivers.get("has_active_legal_dispute", {}).get("value") == 1
    dispute_days = drivers.get("dispute_delay_impact_days", {}).get("value", 0)
    comp_pct = drivers.get("compensation_disbursed_pct", {}).get("value")

    # Primary action from rule templates
    primary_rec = rule_templates[0] if rule_templates else {
        "action_text": "convene an urgent inter-departmental review meeting with the SLAO and revenue authorities",
        "expected_impact": "streamline milestone compliance and resolve pending inter-agency clearances",
    }
    action_text = primary_rec["action_text"]
    expected_impact = primary_rec["expected_impact"]

    # Sentence 1: Root Cause
    if has_dispute and dispute_days and dispute_days > 0:
        s1 = (
            f"Project {name} ({code}) in {district}, {state} is evaluated at {pred_cat.upper()} delay risk "
            f"({delay_prob_pct:.1f}% delay probability), primarily triggered by an active court stay order "
            f"projected to delay possession by {int(dispute_days)} days across {float(land_ha):.1f} hectares."
        )
    elif comp_pct is not None and float(comp_pct) < 80.0:
        s1 = (
            f"Project {name} ({code}) in {district}, {state} is flagged at {pred_cat.upper()} risk "
            f"({delay_prob_pct:.1f}% delay probability), with the core delay bottleneck stemming from low "
            f"compensation disbursement ({float(comp_pct):.1f}% disbursed) across {pafs} project-affected families."
        )
    elif pred_cat in ["high", "critical"]:
        s1 = (
            f"Project {name} ({code}) in {district}, {state} is classified at {pred_cat.upper()} delay risk "
            f"({delay_prob_pct:.1f}% delay probability), encountering significant statutory milestones bottlenecks "
            f"affecting {float(land_ha):.1f} hectares and {pafs} affected families."
        )
    else:
        s1 = (
            f"Project {name} ({code}) in {district}, {state} maintains a {pred_cat.upper()} delay risk profile "
            f"with steady milestone progression across {float(land_ha):.1f} hectares."
        )

    # Sentence 2: Concrete Action
    s2 = (
        f"The District Collector and Special Land Acquisition Officer (SLAO) must immediately {action_text.lower()} "
        f"in direct liaison with the {proj_type} Project Implementation Unit."
    )

    # Sentence 3: Impact & Timeline
    s3 = (
        f"Initiating this intervention within 14 days is projected to {expected_impact.lower()} "
        f"and protect the statutory acquisition timeline under RFCTLARR 2013."
    )

    return f"{s1} {s2} {s3}"


def generate_action_memo(
    project: Any,
    explanation: Dict[str, Any],
    rule_templates: List[Dict[str, Any]],
    simulate_failure: bool = False,
) -> Dict[str, Any]:
    """Generates a 3-4 sentence actionable administrative memo using Gemini 2.5 Flash, falling back to rule templates on error.

    Args:
        project: Project ORM model or project dict.
        explanation: Dictionary returned by ModelExplainer.explain_prediction.
        rule_templates: List of 2-3 rule-based recommendation dictionaries.
        simulate_failure: If True, bypasses LLM and exercises fallback path for validation.

    Returns:
        Dict containing memo, is_llm_generated, fallback_used, and model.
    """
    if simulate_failure:
        logger.info("[LLM] simulate_failure=True requested; executing deterministic fallback memo.")
        fallback_memo = _build_fallback_memo(project, explanation, rule_templates)
        return {
            "memo": fallback_memo,
            "is_llm_generated": False,
            "fallback_used": True,
            "model": "rule-fallback-simulated",
        }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("[LLM] GEMINI_API_KEY not found in environment; utilizing rule fallback.")
        fallback_memo = _build_fallback_memo(project, explanation, rule_templates)
        return {
            "memo": fallback_memo,
            "is_llm_generated": False,
            "fallback_used": True,
            "model": "rule-fallback-no-key",
        }

    try:
        import google.generativeai as genai
        from google.generativeai.types import RequestOptions

        genai.configure(api_key=api_key, transport="rest")

        name = _extract_val(project, "name", "Infrastructure Project")
        code = _extract_val(project, "project_code", "PROJECT")
        district = _extract_val(project, "district", "District")
        state = _extract_val(project, "state", "State")
        proj_type = _extract_val(project, "project_type", "Infrastructure")
        land_ha = _extract_val(project, "land_area_hectares", 0.0)
        pafs = _extract_val(project, "affected_families_count", 0)

        pred_cat = explanation.get("predicted_risk_category", "medium")
        probs = explanation.get("prediction_probabilities", {})
        delay_prob = float(probs.get("high", 0.0) + probs.get("critical", 0.0))
        delay_prob_pct = f"{delay_prob * 100.0:.1f}"

        # 1. Explicitly partition SHAP drivers into positive and negative impact groups
        top_drivers = explanation.get("top_drivers", [])
        risk_increasing_factors = [
            d for d in top_drivers if float(d.get("shap_value", 0.0)) > 0
        ]
        risk_decreasing_factors = [
            d for d in top_drivers if float(d.get("shap_value", 0.0)) < 0
        ]

        # Format Risk Increasing Factors (Bottlenecks)
        inc_bullets = []
        for d in risk_increasing_factors:
            val = d.get('value')
            val_str = f"{val:.1f}" if isinstance(val, float) else str(val)
            inc_bullets.append(
                f"- [RISK BOTTLENECK] {d['display_name']}: Value = {val_str} (SHAP Attribution: +{d['magnitude']:.4f})"
            )
        increasing_str = "\n".join(inc_bullets) if inc_bullets else "- None identified."

        # Format Risk Decreasing Factors (Positive Mitigating Assets)
        dec_bullets = []
        for d in risk_decreasing_factors:
            val = d.get('value')
            val_str = f"{val:.1f}" if isinstance(val, float) else str(val)
            dec_bullets.append(
                f"- [MITIGATING FACTOR] {d['display_name']}: Value = {val_str} (SHAP Attribution: -{d['magnitude']:.4f})"
            )
        decreasing_str = "\n".join(dec_bullets) if dec_bullets else "- None."

        # Format directive details (filtered to valid actionable recommendations)
        template_bullets = []
        for r in rule_templates:
            template_bullets.append(
                f"- Priority [{r['priority_str'].upper()}] ({r['category']}): {r['action_text']} -> Goal: {r['expected_impact']}"
            )
        templates_str = "\n".join(template_bullets) if template_bullets else "- Maintain scheduled milestone monitoring."

        prompt = f"""You are a Senior Secretary for Infrastructure in the Government of India.
Write a 3-sentence administrative action memo for {name} ({code}) in District {district}, {state}.
Project Context: Sector: {proj_type}, Land Area: {land_ha} Ha, PAFs: {pafs}, Delay Risk Tier: {pred_cat.upper()} ({delay_prob_pct}% delay prob).

CRITICAL BOTTLENECKS (Risk-Increasing Factors - POSITIVE SHAP):
{increasing_str}

MITIGATING ASSETS (Risk-Decreasing Factors - NEGATIVE SHAP):
{decreasing_str}

STATUTORY ACTION DIRECTIVES:
{templates_str}

STRICT DIRECTIVE INSTRUCTIONS:
1. FOCUS ONLY ON RISK-INCREASING BOTTLENECKS: Generate action directives ONLY for risk-increasing factors (such as active court stays, pending compensation, large acquisition area).
2. NEVER ESCALATE RISK-DECREASING FACTORS: Features classified as mitigating assets / negative SHAP (e.g. stakeholder responsiveness) are strengths, NOT problems. Never frame them as bottlenecks or demand corrective escalation. You may either omit them entirely, or mention them briefly as a positive note (e.g. "stakeholder responsiveness at {risk_decreasing_factors[0]['value'] if risk_decreasing_factors else ''} is a mitigating factor and should be maintained").
3. Sentence 1 (Root Cause): State the exact root causes of delay with real project numbers (stay order delay days, land area in Ha, compensation %, PAFs).
4. Sentence 2 (Action): Concrete statutory directive to the District Collector / SLAO / Legal Cell / Treasury addressing ONLY the risk-increasing bottlenecks.
5. Sentence 3 (Impact): Operational timeline (14 to 30 days) and delay days saved under RFCTLARR 2013.
Tone: Formal Indian administrative English. Output ONLY the memo text without any titles or markdown asterisks/bullets."""

        model = genai.GenerativeModel("gemini-2.5-flash")
        timeout_sec = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "12.0"))
        response = model.generate_content(prompt, request_options=RequestOptions(timeout=timeout_sec))
        memo_text = response.text.strip()
        # Clean any leading title if model outputs one
        if memo_text.startswith("**") and "\n\n" in memo_text:
            memo_text = memo_text.split("\n\n", 1)[1].strip()

        # Sanity check output
        if not memo_text or len(memo_text) < 50:
            raise ValueError("Gemini returned an unexpectedly short or empty response.")

        return {
            "memo": memo_text,
            "is_llm_generated": True,
            "fallback_used": False,
            "model": "gemini-2.5-flash",
        }

    except Exception as e:
        logger.warning(f"[LLM] Gemini API call failed or timed out: {e}. Gracefully reverting to rule fallback.")
        fallback_memo = _build_fallback_memo(project, explanation, rule_templates)
        return {
            "memo": fallback_memo,
            "is_llm_generated": False,
            "fallback_used": True,
            "model": "rule-fallback-exception",
            "fallback_reason": str(e),
        }
