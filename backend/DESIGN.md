# Design — Usage Metering & Billing Engine

## Problem
SaaS backend answering three questions per tenant: how much have they used,
what does it cost, and have they hit their plan limit — with correctness
guarantees under retries and concurrent requests.

## Data model
- tenants — customer organization, isolation boundary for all billing data
- profiles — auth.users(id) 1:1, links a user to their tenant
- plans — Free / Pro, pinned quota + limit values
- subscriptions — tenant's current plan + Stripe sync fields (customer_id, subscription_id)
- usage_events — one row per billable action, unique(idempotency_key) enforced at the DB level
- token_usage_details — per-event AI token breakdown + computed cost_cents, child of usage_events
- usage_rollups — monthly aggregate per (tenant_id, event_type), unique constraint enables safe upsert on rerun
- stripe_events — processed webhook event IDs, primary-key-enforced dedup

## API surface
See capstone.yaml for the full endpoint list. Auth uses Supabase JWTs via
`Authorization: Bearer <token>`; a single `get_current_tenant` dependency
resolves every request down to a verified `(user_id, tenant_id)` pair —
no endpoint trusts a client-supplied tenant_id.

## Layer sketch
Router (HTTP, validation) → Service (meter_service, quota_service,
pricing_service, stripe_service, rollup_service — business logic) →
Supabase client (persistence). Routers never touch the database directly.

## Idempotency strategy
Client sends `Idempotency-Key` header on `/generate`. Server checks
`usage_events.idempotency_key` (unique-constrained) before any quota check
or insert; existing key → return cached result immediately, no quota
re-evaluation. This guarantees a replay never double-counts and never
fails a request that already succeeded, even if the tenant is later over
quota.

## Non-goal
No invoicing, proration, or overage billing in this core build — quota
enforcement is hard-stop only (429/402), per the brief's realistic-scope
guidance.