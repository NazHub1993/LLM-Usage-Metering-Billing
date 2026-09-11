# LLM-Usage Metering & Billing Engine using STRIPE 

FastAPI backend for the FlyRank capstone: metering, quota enforcement,
AI-token pricing, and Stripe test-mode subscription billing.

## Architecture

    Client → Router (validation) → Service layer (business logic) → Supabase (Postgres + Auth)
                                                                    → Stripe (test mode, webhooks)

    JWT → user_id → profile → tenant_id   (every request resolves through this chain)

## Setup
1. `python -m venv venv && source venv/bin/activate` (Windows: `venv\Scripts\activate`)
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`, fill in your Supabase + Stripe test-mode keys
4. Run the SQL in `schema.sql` [create this file from your Phase 2/5/8 CREATE TABLE
   statements, consolidated] against your Supabase project
5. `uvicorn app.main:app --reload`
6. `curl localhost:8000/health` → `{"status": "ok"}`

## Plans
| Plan | API calls/month | AI tokens/month |
|------|-----------------|------------------|
| Free | 1,000           | 100,000          |
| Pro  | 10,000          | 1,000,000        |

## Webhook testing locally

stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
stripe trigger checkout.session.completed



## Limitations
- No automated test suite — evidence in EVIDENCE.md is manual (curl/Postman
  transcripts + Supabase table checks)
- customer.subscription.updated is recorded (dedup-safe) but not yet acted
  on; only checkout.session.completed (upgrade) and
  customer.subscription.deleted (downgrade) trigger a plan change
- No invoicing, proration, or overage billing (out of scope per brief)
- Pricing constants are illustrative placeholders, not tied to a real
  provider's live rate card
