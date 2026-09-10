from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from app.core.deps import TenantContext, get_current_tenant
from app.service import meter_service, quota_service
from app.core.client import supabase


router = APIRouter(prefix="/api/v1", tags=["generate"])


class GenerateRequest(BaseModel):
    event_type: str = "api_call"
    quantity: int = 1


@router.post("/generate")
def generate(payload: GenerateRequest,
             ctx: TenantContext = Depends(get_current_tenant),
             idempotency_key: str = Header(..., alias="Idempotency-Key"),):

    idempotency_check = (
        supabase.table("usage_events")
        .select("*")
        .eq("idempotency_key", idempotency_key)
        .execute()
    )

    if idempotency_check.data:
        return {"status": "ok (idempotent replay)", "usage_event": idempotency_check.data[0]}
    allowed, used, limit = quota_service.check_quota(
        ctx.tenant_id, payload.event_type, payload.quantity)

    if not allowed:
        raise HTTPException(
            status_code=429, detail="Usage quota exceeded for this billing period")

    result, was_created = meter_service.record_usage(
        ctx.tenant_id, payload.event_type, payload.quantity, idempotency_key
    )

    return {"status": "ok", "usage_event": result, "used": used + payload.quantity, "limit": limit}
