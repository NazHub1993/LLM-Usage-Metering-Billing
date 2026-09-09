from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.deps import get_current_tenant, TenantContext
from app.core.client import supabase

router=APIRouter(prefix="/api/v1/profile")

class ProfileUpdateRequest(BaseModel):
    name:str | None=None

@router.get("")
def get_profile(ctx:TenantContext=Depends(get_current_tenant)):
    result=supabase.table("profiles").select("*").eq("id",ctx.user_id).single().execute()
    return result.data


@router.patch("")
def update_profile(payload:ProfileUpdateRequest, ctx:TenantContext=Depends(get_current_tenant)):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    result=supabase.table("profiles").update(updates).eq("id",ctx.user_id).execute()
    return result.data[0]

