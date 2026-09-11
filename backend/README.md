# LLM-Usage-Metering-Billing Engine

A backend service that answers the three questions every SaaS product needs answered: how much has a customer used, what should they pay, and have they hit their plan's limit.

Built for the FlyRank Internship Backend Track capstone. FastAPI + Supabase (Auth + Postgres) + Stripe (test mode), with idempotent usage metering, quota enforcement, AI-token pricing, and signature-verified Stripe webhooks.

## What this does

- **Multi-tenant auth** — every user belongs to a tenant; every billable action, quota, and subscription is scoped to that tenant, never leaking across tenants
- **Idempotent metering** — the same billable request retried with the same `Idempotency-Key` records exactly one usage event, never a duplicate
- **Quota enforcement** — requests are checked against the tenant's plan *before* being recorded; boundary cases (exactly at the limit) are handled precisely, with `429` responses that explain why
- **AI-token pricing** — input, cached input, output, and reasoning tokens are priced correctly per the real-world rule that reasoning tokens bill at the output rate, not separately; cost is stored as integer cents, never floats
- **Stripe subscriptions (test mode)** — Checkout flow to upgrade Free → Pro, with a webhook handler that verifies signatures, deduplicates events, and syncs the tenant's plan
- **Usage rollups** — a background job aggregates raw usage events into per-tenant monthly summaries, feeding `GET /usage`

## Architecture
Client
│
▼
Router layer (FastAPI) — request validation, HTTP concerns only
│
▼
Service layer — meter_service, quota_service, pricing_service,
stripe_service, rollup_service (business logic)
│
▼
Supabase (Postgres + Auth) Stripe (test mode)
│
▼
Signed webhook → /api/v1/webhooks/stripe


**Auth chain, resolved on every authenticated request:**
Authorization: Bearer <JWT> → user_id → profile → tenant_id

No endpoint ever trusts a client-supplied `tenant_id` — it's always derived server-side from the verified token.

## Tech stack

| Layer | Choice |
|---|---|
| Language / framework | Python 3.11+ / FastAPI |
| Database | PostgreSQL, hosted via Supabase |
| Auth | Supabase Auth (JWT) |
| Payments | Stripe, test mode only |
| Background jobs | APScheduler (in-process scheduler) |
| Local webhook delivery | Stripe CLI |

## Project structure
LLM-Usage-Metering-Billing/
backend/
├── app/
│ ├── main.py # FastAPI entry point, router registration, scheduler startup
│ ├── core/
│ │ ├── config.py # Settings (env vars)
│ │ ├── client.py # Supabase client instance
│ │ ├── deps.py # get_current_tenant dependency
│ │ └── pricing_constants.py # Pinned per-1k-token prices
│ ├── routers/
│ │ ├── auth.py # register, login, refresh, logout, me
│ │ ├── profile.py # GET/PATCH profile
│ │ ├── generate.py # POST /generate — the core billable endpoint
│ │ ├── usage.py # GET /usage
│ │ ├── billing.py # POST /billing/checkout, GET /billing/success
│ │ ├── webhooks.py # POST /webhooks/stripe
│ │ └── admin.py # POST /admin/rollup/run
│ └── services/
│ ├── meter_service.py # Idempotent usage recording
│ ├── quota_service.py # Usage + limit checks
│ ├── pricing_service.py # Token cost calculation
│ ├── stripe_service.py # Checkout session creation
│ └── rollup_service.py # Monthly usage/cost aggregation
├── tests/
├── schema.sql # All CREATE TABLE statements, run once against Supabase
├── .env.example
├── .gitignore
├── README.md
├── DESIGN.md
├── EVIDENCE.md
├── BUILDLOG.md
└── capstone.yaml
**Prerequisites:** Python 3.11+, a free [Supabase](https://supabase.com) project, a free [Stripe](https://stripe.com) account in test mode, the [Stripe CLI](https://stripe.com/docs/stripe-cli).

**1. Clone and enter the project**
```bash
git clone <your-repo-url>
cd usage-metering-billing-engine
```

**2. Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up Supabase**
- Create a project at supabase.com
- In the SQL Editor, run everything in `schema.sql` — this creates `tenants`, `profiles`, `plans`, `subscriptions`, `usage_events`, `token_usage_details`, `usage_rollups`, and `stripe_events`, and seeds the Free/Pro plans
- From Project Settings → API, copy your Project URL, `anon` key, and `service_role` key

**5. Set up Stripe (test mode)**
- Create a Product + recurring Price for "Pro" in the Stripe Dashboard (test mode) — copy the Price ID
- From Developers → API keys, copy your test secret key
- Run `stripe login`, then `stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe` — copy the `whsec_...` signing secret it prints

**6. Configure environment**
```bash
cp .env.example .env
```
Fill in `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_PRO_PRICE_ID`, `STRIPE_WEBHOOK_SECRET`.

**7. Run it**
```bash
uvicorn app.main:app --reload
```
```bash
curl localhost:8000/health
# {"status": "ok"}
```

**8. Keep Stripe CLI forwarding running** (separate terminal, for webhook testing)
```bash
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
```

## Plans

| Plan | API calls / month | AI tokens / month |
|---|---|---|
| Free | 1,000 | 100,000 |
| Pro | 10,000 | 1,000,000 |

## API reference

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | — | Liveness check |
| POST | `/api/v1/auth/register` | — | Create user, auto-provisions a tenant + Free subscription |
| POST | `/api/v1/auth/login` | — | Returns access + refresh tokens |
| POST | `/api/v1/auth/refresh` | — | Refresh an access token |
| POST | `/api/v1/auth/logout` | — | Sign out |
| GET | `/api/v1/auth/me` | Bearer | Current user + tenant |
| GET | `/api/v1/profile` | Bearer | Get profile |
| PATCH | `/api/v1/profile` | Bearer | Update profile |
| POST | `/api/v1/generate` | Bearer + `Idempotency-Key` header | Record billable usage (api_call or ai_tokens), quota-checked |
| GET | `/api/v1/usage` | Bearer | Current plan, rolled-up usage, limits |
| POST | `/api/v1/billing/checkout` | Bearer | Create a Stripe Checkout session for Pro |
| GET | `/api/v1/billing/success` | — | Checkout redirect target |
| POST | `/api/v1/webhooks/stripe` | Stripe signature | Signature-verified, deduplicated webhook handler |
| POST | `/api/v1/admin/usage/rollup` | — | Manually trigger the usage rollup job (also runs on a 5-minute schedule) |

### Example: recording usage
```bash
curl -X POST localhost:8000/api/v1/generate \
  -H "Authorization: Bearer <token>" \
  -H "Idempotency-Key: <unique-uuid-per-request>" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"ai_tokens","input_tokens":2000,"cached_input_tokens":5000,"output_tokens":500,"reasoning_tokens":500}'
```
Retrying with the **same** `Idempotency-Key` returns the original result — no duplicate event, no double count.

## Webhook testing locally

```bash
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
stripe trigger checkout.session.completed
```
See `EVIDENCE.md` for verified transcripts of signature rejection and duplicate-event handling.

## Evidence

Every requirement in the capstone brief has a corresponding proof — real request/response pairs and database checks — in `EVIDENCE.md`. Design decisions and data model reasoning are in `DESIGN.md`. AI-assisted development is logged honestly in `BUILDLOG.md`, including real bugs introduced and fixed along the way.

## Limitations

- No automated test suite — all evidence is manual (curl/Postman transcripts plus direct Supabase table checks)
- `customer.subscription.updated` events are received and deduplicated but don't currently trigger any state change; only `checkout.session.completed` (upgrade) and `customer.subscription.deleted` (downgrade to Free) update the tenant's plan
- No invoicing, proration, or overage billing — out of scope per the capstone's realistic-scope guidance
- Pricing constants in `pricing_constants.py` are illustrative placeholders, not tied to any real AI provider's live rate card
- Stripe test-mode account was created via [see BUILDLOG.md for details, since Bangladesh isn't among Stripe's directly supported account countries]


