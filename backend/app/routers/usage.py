from fastapi import APIRouter, Depends
from app.core.deps import TenantContext, get_current_tenant
from app.core.client import supabase

router = APIRouter(prefix="/api/v1", tags=["usage"])


@router.get("/usage")
def get_usage(ctx: TenantContext = Depends(get_current_tenant)):
    rollups = supabase.table("usage_rollups").select(
        "*").eq("tenant_id", ctx.tenant_id).execute()
    sub = supabase.table("subscriptions").select("plan_id").eq(
        "tenant_id", ctx.tenant_id).single().execute()
    plan = supabase.table("plans").select(
        "*").eq("id", sub.data["plan_id"]).single().execute()

    return {
        "plan": plan.data["name"],
        "usage": rollups.data,
        "limits": {
            "api_call_limit": plan.data["api_call_limit"],
            "ai_token_limit": plan.data["ai_token_limit"],
        }
    }
