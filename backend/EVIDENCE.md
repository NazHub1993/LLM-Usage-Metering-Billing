# Evidence

## Probe 1 — Idempotency
Same billable request sent twice with one Idempotency-Key → exactly one
usage_event; second response mirrors the first.

[NEEDS YOUR OWN SCREENSHOT — you confirmed this worked during Phase 4 but
I don't have the literal request/response pasted in our conversation.
Send the same /generate request twice with the same Idempotency-Key,
paste both responses + the Supabase usage_events row count here.]

## Probe 2 — Quota boundary
Tenant driven to exact quota → boundary request allowed, next one rejected
with 429 and a clear message.

[NEEDS YOUR OWN SCREENSHOT — same as above, this was discussed and you
confirmed it during Phase 4 testing but the literal boundary output
(request #5 allowed, #6 → 429) wasn't pasted into this conversation.
Re-run the limit=5 test from Phase 4 Step 2-3 and paste the actual
responses.]

## Probe 3 — Stripe Checkout → webhook → Free/Pro sync
Real Checkout completed in Stripe test mode; webhook received
checkout.session.completed, resolved tenant via client_reference_id,
updated subscriptions.plan_id to Pro:

    Tenant ID: 37ed5fca-1396-4cb3-8c0e-d27f0cba6301
    Updated Subscription: [{'tenant_id': '37ed5fca-...',
      'plan_id': '3bed5a3f-6091-401d-a79e-6d349e63f640', 'status': 'active', ...}]

Confirmed via GET /usage immediately after:

    {"plan": "Pro", "limits": {"api_call_limit": 10000, "ai_token_limit": 1000000}}

## Probe 4 — Webhook security
**Forged signature → 400, nothing changed:**

    curl -X POST localhost:8000/api/v1/webhooks/stripe -H "Content-Type: application/json" \
      -H "stripe-signature: t=1234,v1=fake" -d "{\"fake\":\"event\"}"
    → {"detail":"Invalid webhook signature"}

**Real event replayed twice → processed once:**

    First delivery: full handler ran, subscription updated.
    stripe events resend evt_1UEN7SDdlatnuW4HV8fthqbI (second delivery):
    → "Event already processed: evt_1UEN7SDdlatnuW4HV8fthqbI"
    → 200 OK, no second "Updated Subscription" log line
    → stripe_events row count for this event ID: 1 (confirmed via SQL)

## Probe 5 — Pricing correctness
Input: input_tokens=2000, cached_input_tokens=5000, output_tokens=500,
reasoning_tokens=500. Hand-calculated expected cost: $1.09 → 109 cents.

    Actual token_usage_details.cost_cents: 109 ✓

Rollup correctly aggregates cost across events (post-fix):

    total_quantity: 10037, total_cost_cents: 620  (ai_tokens, tenant 027c61ab-...)
    total_quantity: 2000,  total_cost_cents: 75   (ai_tokens, tenant 37ed5fca-...)

GET /usage reflects these rollup values under "usage".