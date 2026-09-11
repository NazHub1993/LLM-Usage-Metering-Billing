from fastapi import APIRouter, Depends
from app.core.deps import TenantContext, get_current_tenant
from app.service import stripe_service

router=APIRouter(prefix="/api/v1/billing")


@router.post("/checkout")
def checkout(ctx:TenantContext = Depends(get_current_tenant)):
    url=stripe_service.create_checkout_session(ctx.tenant_id,ctx.email)
    return {"checkout_url":url}

@router.get("/success")
def checkout_success(session_id: str):
    return {"status": "subscription activated", "session_id": session_id}
