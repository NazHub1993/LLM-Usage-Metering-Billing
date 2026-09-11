from fastapi import APIRouter, HTTPException

from app.service.rollup_service import run_usage_rollup

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.post("/usage/rollup")
def trigger_usage_rollup():
    success = run_usage_rollup()

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Usage rollup failed"
        )

    return {
        "message": "Usage rollup completed successfully"
    }
