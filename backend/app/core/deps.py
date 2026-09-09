from fastapi import HTTPException, Header
from app.core.client import supabase


class TenantContext:
    def __init__(self, user_id: str, email: str, tenant_id: str):
        self.user_id = user_id
        self.email = email
        self.tenant_id = tenant_id


def get_current_tenant(authorization: str = Header(...)) -> TenantContext:

    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or malformed authorization header")

    token = authorization.split(" ", 1)[1]
    user_result = supabase.auth.get_user(token)

    if user_result.user is None:
        raise HTTPException(401, "Invalid or expired token")

    user_id = user_result.user.id
    email = user_result.user.email

    profile = (
        supabase.table("profiles")
        .select("tenant_id")
        .eq("id", user_id)
        .single()
        .execute()
    )

    if not profile.data:
        raise HTTPException(404, "Profile not found for this user")

    return TenantContext(user_id=user_id, email=email, tenant_id=profile.data["tenant_id"])
