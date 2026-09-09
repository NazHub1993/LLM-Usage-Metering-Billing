from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.client import supabase
from supabase_auth.errors import AuthApiError

router = APIRouter(prefix="/api/v1/auth")


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(payload: RegisterRequest):

    # 1. Create Auth User
    try:
        result = supabase.auth.sign_up(
            {
                "email": payload.email,
                "password": payload.password
            }
        )
    except AuthApiError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, "Registration failed")

    if result.user is None:
        raise HTTPException(400, "Registration failed")

    user_id = result.user.id

    # 2. Create Tenant
    try:
        tenant = supabase.table("tenants").insert(
            {"name": f"{payload.name or payload.email}'s Workspace"}
        ).execute()
    except Exception as e:
        raise HTTPException(500, "Failed to create workspace")

    if not tenant.data:
        raise HTTPException(500, "Workspace creation failed")

    tenant_id = tenant.data[0]["id"]

    # 3. Create Profile
    try:
        supabase.table("profiles").insert({
            "id": user_id,
            "tenant_id": tenant_id,
            "name": payload.name
        }).execute()
    except Exception as e:
        raise HTTPException(500, "Failed to create profile")

    # 4. Get Free Plan
    try:
        free_plan = supabase.table("plans").select("id").eq(
            "name", "Free"
        ).single().execute()
    except Exception as e:
        raise HTTPException(500, "Failed to find Free plan")

    if not free_plan.data:
        raise HTTPException(500, "Free plan not found")

    # 5. Create Subscription
    try:
        supabase.table("subscriptions").insert(
            {
                "tenant_id": tenant_id,
                "plan_id": free_plan.data["id"]
            }
        ).execute()
    except Exception as e:
        raise HTTPException(500, "Failed to create subscription")

    return {
        "user_id": user_id,
        "tenant_id": tenant_id
    }


@router.post("/login")
def login(payload: LoginRequest):

    try:
        result = supabase.auth.sign_in_with_password(
            {
                "email": payload.email,
                "password": payload.password
            }
        )
    except AuthApiError as e:
        raise HTTPException(401, str(e))
    except Exception as e:
        raise HTTPException(500, "Login failed")

    if result.session is None:
        raise HTTPException(401, "Invalid Credentials")

    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token
    }


@router.post("/refresh")
def refresh(refresh_token: str):

    try:
        result = supabase.auth.refresh_session(refresh_token)
    except AuthApiError as e:
        raise HTTPException(401, str(e))
    except Exception as e:
        raise HTTPException(500, "Token refresh failed")

    if result.session is None:
        raise HTTPException(401, "Invalid refresh token")

    return {
        "access_token": result.session.access_token
    }


@router.post("/logout")
def logout():

    try:
        supabase.auth.sign_out()
    except AuthApiError as e:
        raise HTTPException(401, str(e))
    except Exception as e:
        raise HTTPException(500, "Logout failed")

    return {"status": "logged out"}


@router.get("/me")
def me(access_token: str):

    try:
        result = supabase.auth.get_user(access_token)
    except AuthApiError as e:
        raise HTTPException(401, str(e))
    except Exception as e:
        raise HTTPException(500, "Failed to get user")

    if result.user is None:
        raise HTTPException(401, "Invalid Token")

    return {
        "id": result.user.id,
        "email": result.user.email
    }
