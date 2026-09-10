from app.core.client import supabase


def get_current_usage(tenant_id: str, event_type: str) -> int:

    result = (supabase.table("usage_events")
              .select("quantity")
              .eq("tenant_id", tenant_id)
              .eq("event_type", event_type)
              .execute())

    return sum(row['quantity'] for row in result.data)


def get_plan_limit(tenant_id: str, event_type: str) -> int:
    sub = (
        supabase.table("subscriptions")
        .select("plan_id")
        .eq("tenant_id", tenant_id)
        .single().execute()

    )
    plan = (
        supabase.table("plans")
        .select("*")
        .eq("id", sub.data["plan_id"])
        .single().execute()

    )

    return plan.data["api_call_limit"] if event_type == "api_call" else plan.data["ai_token_limit"]


def check_quota(tenant_id: str, event_type: str, requested_quantity: int) -> tuple[bool, int, int]:
    used = get_current_usage(tenant_id, event_type)
    limit = get_plan_limit(tenant_id, event_type)
    print("Used till now: ",used)
    print("The amount you want: ",used+requested_quantity)
    allowed = (used+requested_quantity) <= limit
    return allowed, used, limit
