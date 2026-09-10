from app.core.client import supabase


def record_usage(tenant_id: str, event_type: str, quantity: int, idempotency_key: str):

    existing =(supabase.table("usage_events")
    .select("*")
    .eq("idempotency_key", idempotency_key)
    .execute())

    if existing.data:
        return existing.data[0], False

    result = (supabase.table("usage_events")
    .insert(
        {
            "tenant_id": tenant_id,
            "event_type": event_type,
            "quantity": quantity,
            "idempotency_key": idempotency_key
        }
    ).execute())
    return result.data[0], True
