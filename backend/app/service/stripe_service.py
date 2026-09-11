import stripe 
from app.core.config import settings

stripe.api_key=settings.stripe_secret_key

def create_checkout_session(tenant_id:str, customer_email:str) -> str:
    session=stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price":settings.stripe_pro_price_id,"quantity":1}],
        success_url="http://localhost:8000/api/v1/billing/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:8000/api/v1/billing/cancel",
        client_reference_id=tenant_id,
        customer_email=customer_email
    )

    return session.url