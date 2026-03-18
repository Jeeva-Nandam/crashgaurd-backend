from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import pandas as pd

from app.models.schemas import CrashInput, AnalysisSaveRequest
from app.utils.csv_validator import validate_csv
from app.services.calculations import (
    revenue_trend, expense_trend, burn_rate,
    runway_analysis, calculate_churn_rate
)
from app.services.risk_engine import (
    revenue_risk_score, expense_risk_score, runway_risk_score,
    churn_risk_score, risk_label, predict_zero_cash_date
)
from app.services.recommendations import (
    generate_explanation, decision_recommendations, improvement_projection
)
from app.services.analysis_service import (
    save_analysis, get_user_analyses, get_analysis_by_id, delete_analysis
)
from app.core.dependencies import get_verified_user

router = APIRouter(prefix="/analysis", tags=["Analysis"])


# ── Core analysis logic (reusable) ────────────────────────────────────────────
def run_analysis(data: CrashInput) -> dict:
    rev_trend_value, rev_label = revenue_trend(data.revenue)
    exp_trend_value, exp_label = expense_trend(data.expenses)

    avg_burn = burn_rate(data.revenue, data.expenses)
    runway_days, runway_status = runway_analysis(data.cash_in_hand, avg_burn)

    churn_rates = calculate_churn_rate(data.customers)

    rev_risk = revenue_risk_score(rev_trend_value)
    exp_risk = expense_risk_score([rev_trend_value], [exp_trend_value])
    run_risk = runway_risk_score(runway_days)
    ch_risk = churn_risk_score(churn_rates)

    final_score = round((rev_risk + exp_risk + run_risk + ch_risk) / 4)

    signals = {
        "revenue_risk": rev_risk,
        "expense_risk": exp_risk,
        "churn_risk": ch_risk,
        "runway_risk": run_risk,
    }

    crash_date, crash_reason = predict_zero_cash_date(
        data.cash_in_hand, data.revenue, data.expenses
    )

    improvement = improvement_projection(
        data.cash_in_hand, data.revenue, data.expenses
    )

    return {
        "crash_score": final_score,
        "risk_level": risk_label(final_score),
        "metrics": {
            "revenue_trend": {"percentage": rev_trend_value, "status": rev_label},
            "expense_trend": {"percentage": exp_trend_value, "status": exp_label},
            "burn_rate": {"amount_per_month": avg_burn},
            "runway": {"days_remaining": runway_days, "status": runway_status},
        },
        "predicted_zero_cash_date": crash_date,
        "crash_reason": crash_reason,
        "explanation": generate_explanation(signals),
        "recommended_actions": decision_recommendations(signals),
        "improvement_projection": improvement,
        "risk_sub_scores": signals,
        # Chart data
        "months": [f"M{i+1}" for i in range(len(data.revenue))],
        "revenue": data.revenue,
        "expenses": data.expenses,
        "churn_rate": churn_rates,
        "customers": data.customers,
    }


# ── POST /analysis/analyze — run + save ───────────────────────────────────────
@router.post("/analyze")
async def analyze(
    payload: AnalysisSaveRequest,
    current_user: dict = Depends(get_verified_user),
):
    """
    Run the crash analysis and automatically save it to the user's history.
    """
    result = run_analysis(payload.input_data)
    saved = await save_analysis(current_user["id"], payload.label, result)

    return {
        "analysis_id": saved["id"],
        "label": saved["label"],
        "created_at": saved["created_at"],
        **result,
    }


# ── POST /analysis/upload-csv — CSV upload + save ─────────────────────────────
@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    cash_in_hand: float = Form(...),
    label: str = Form(None),
    current_user: dict = Depends(get_verified_user),
):
    try:
        df = pd.read_csv(file.file)

        errors = validate_csv(df)
        if errors:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "issues": errors}
            )

        revenue = df["revenue"].tolist()
        expenses = df["expenses"].tolist()
        customers = df["customers"].tolist()

        data = CrashInput(
            revenue=revenue,
            expenses=expenses,
            cash_in_hand=cash_in_hand,
            customers=customers,
        )

        result = run_analysis(data)
        saved = await save_analysis(current_user["id"], label, result)

        return {
            "analysis_id": saved["id"],
            "label": saved["label"],
            "created_at": saved["created_at"],
            **result,
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


# ── GET /analysis/history — user's past analyses ──────────────────────────────
@router.get("/history")
async def get_history(
    limit: int = 20,
    current_user: dict = Depends(get_verified_user),
):
    """Return the authenticated user's analysis history (latest first)."""
    analyses = await get_user_analyses(current_user["id"], limit=limit)
    return {"count": len(analyses), "analyses": analyses}


# ── GET /analysis/{id} — single analysis ─────────────────────────────────────
@router.get("/{analysis_id}")
async def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_verified_user),
):
    analysis = await get_analysis_by_id(analysis_id, current_user["id"])
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return analysis


# ── DELETE /analysis/{id} ─────────────────────────────────────────────────────
@router.delete("/{analysis_id}")
async def delete_user_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_verified_user),
):
    deleted = await delete_analysis(analysis_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return {"message": "Analysis deleted."}
