from app.core.client import supabase
from app.core.config import settings
import stripe
from fastapi import APIRouter, Request, HTTPException


router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["webhooks"]
)


@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # 1. Verify Stripe webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.stripe_webhook_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook signature"
        )

    print("Received Stripe Event:", event["type"])

    # 2. Deduplication
    # Check whether this exact Stripe event was already processed
    existing = (
        supabase
        .table("stripe_events")
        .select("*")
        .eq("id", event["id"])
        .execute()
    )

    if existing.data:
        print("Event already processed:", event["id"])
        return {"status": "already processed"}

    # 3. Record the event before processing it
    supabase.table("stripe_events").insert({
        "id": event["id"],
        "event_type": event["type"]
    }).execute()

    # 4. Handle successful Checkout
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        tenant_id = session.client_reference_id
        customer_id = session.customer
        subscription_id = session.subscription

        print("Checkout Session ID:", session.id)
        print("Customer ID:", customer_id)
        print("Subscription ID:", subscription_id)
        print("Tenant ID:", tenant_id)

        # Make sure the Checkout Session contains our tenant ID
        if not tenant_id:
            print(
                f"WARNING: checkout.session.completed with no "
                f"client_reference_id. Session: {session.id}"
            )
            return {"status": "ignored - no tenant reference"}

        # 5. Find the Pro plan
        pro_plan = (
            supabase
            .table("plans")
            .select("id")
            .eq("name", "Pro")
            .single()
            .execute()
        )

        if not pro_plan.data:
            raise HTTPException(
                status_code=500,
                detail="Pro plan not found"
            )

        pro_plan_id = pro_plan.data["id"]

        # 6. Upgrade the tenant subscription
        updated = (
            supabase
            .table("subscriptions")
            .update({
                "plan_id": pro_plan_id,
                "status": "active",
                "stripe_customer_id": customer_id,
                "stripe_subscription_id": subscription_id
            })
            .eq("tenant_id", tenant_id)
            .execute()
        )

        print("Updated Subscription:", updated.data)

    return {"status": "processed"}
