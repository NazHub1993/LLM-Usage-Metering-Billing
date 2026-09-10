from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from app.core.deps import TenantContext, get_current_tenant
from app.service import meter_service, quota_service, pricing_service
from app.core.client import supabase



router = APIRouter(prefix="/api/v1", tags=["generate"])


class GenerateRequest(BaseModel):
    event_type: str = "api_call"
    quantity: int = 1
    input_tokens : int =0
    cached_input_tokens:int =0
    output_tokens:int =0
    reasoning_tokens: int =0


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


    if payload.event_type=="ai_tokens":
        effective_quantity = (
            payload.input_tokens+ payload.cached_input_tokens+ payload.reasoning_tokens+ payload.output_tokens
        )
    else:
        effective_quantity=payload.quantity

    allowed, used, limit = quota_service.check_quota(
        ctx.tenant_id, payload.event_type, effective_quantity)

    if not allowed:
        raise HTTPException(
            status_code=429, detail="Usage quota exceeded for this billing period")

    result, was_created = meter_service.record_usage(
        ctx.tenant_id, payload.event_type, effective_quantity, idempotency_key
    )

    if payload.event_type == "ai_tokens":
        cost_cents=pricing_service.calculate_cost_cents(
            payload.input_tokens,payload.cached_input_tokens,payload.reasoning_tokens,payload.output_tokens
        )
        supabase.table("token_usage_details").insert({
            "usage_event_id": result["id"],
            "input_tokens": payload.input_tokens,
            "cached_input_tokens": payload.cached_input_tokens,
            "output_tokens": payload.output_tokens,
            "reasoning_tokens": payload.reasoning_tokens,
            "cost_cents": cost_cents,
        }).execute()

    return {"status": "ok", "usage_event": result, "used": used + effective_quantity, "limit": limit}
