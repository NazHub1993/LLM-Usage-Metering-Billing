# LLM Usage Metering & Billing Engine

A backend service that answers the three questions every SaaS product needs answered:

1. How much has a customer used?
2. What should they pay?
3. Have they hit their plan's limit?

Built for the FlyRank Internship Backend Track capstone.

The project uses **FastAPI + Supabase (Auth + PostgreSQL) + Stripe (test mode)** and implements idempotent usage metering, quota enforcement, AI-token pricing, subscription management, and signature-verified Stripe webhooks.

## What This Does

* **Multi-tenant authentication** — every user belongs to a tenant. Billable actions, quotas, usage, and subscriptions are scoped to that tenant.
* **Idempotent usage metering** — retrying the same billable request with the same `Idempotency-Key` records exactly one usage event.
* **Quota enforcement** — requests are checked against the tenant's plan limits before usage is recorded. Requests that exceed a limit return `429 Too Many Requests`.
* **AI-token pricing** — input, cached input, output, and reasoning tokens are priced correctly. Reasoning tokens are billed at the output-token rate.
* **Integer-based cost storage** — monetary costs are stored as integer cents rather than floating-point values.
* **Stripe subscriptions** — supports Free → Pro upgrades through Stripe Checkout in test mode.
* **Webhook processing** — Stripe webhook signatures are verified and duplicate events are rejected using event IDs.
* **Usage rollups** — raw usage events are aggregated into monthly per-tenant summaries.
* **Background processing** — APScheduler periodically runs the usage rollup job.

## Architecture

```text
                         Client
                           |
                           v
                +----------------------+
                |   FastAPI Routers    |
                | Request validation   |
                | HTTP concerns        |
                +----------+-----------+
                           |
                           v
                +----------------------+
                |    Service Layer     |
                |                      |
                | meter_service        |
                | quota_service        |
                | pricing_service      |
                | stripe_service       |
                | rollup_service       |
                +----------+-----------+
                           |
                           v
              +--------------------------+
              |        Supabase          |
              |                          |
              | PostgreSQL + Supabase    |
              | Auth                     |
              +--------------------------+
                           ^
                           |
                  Stripe Webhooks
                           |
                           v
              POST /api/v1/webhooks/stripe
```

### Authentication Flow

Every authenticated request follows this chain:

```text
Authorization: Bearer <JWT>
            |
            v
         user_id
            |
            v
         profile
            |
            v
        tenant_id
```

The API never trusts a client-supplied `tenant_id`.

The tenant is always derived server-side from the verified authentication token.

## Tech Stack

| Layer           | Technology              |
| --------------- | ----------------------- |
| Language        | Python 3.11+            |
| Framework       | FastAPI                 |
| Database        | PostgreSQL via Supabase |
| Authentication  | Supabase Auth / JWT     |
| Payments        | Stripe (test mode)      |
| Background Jobs | APScheduler             |
| Local Webhooks  | Stripe CLI              |
| API Testing     | curl / Postman          |

## Project Structure

```text
LLM-Usage-Metering-Billing/
│
├── backend/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── client.py
│   │   │   ├── deps.py
│   │   │   └── pricing_constants.py
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── profile.py
│   │   │   ├── generate.py
│   │   │   ├── usage.py
│   │   │   ├── billing.py
│   │   │   ├── webhooks.py
│   │   │   └── admin.py
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── meter_service.py
│   │       ├── quota_service.py
│   │       ├── pricing_service.py
│   │       ├── stripe_service.py
│   │       └── rollup_service.py
│   │
│   ├── tests/
│   │
│   ├── schema.sql
│   ├── .env.example
│   ├── .gitignore
│   ├── requirements.txt
│   ├── README.md
│   ├── DESIGN.md
│   ├── EVIDENCE.md
│   ├── BUILDLOG.md
│   └── capstone.yaml
│
└── .gitignore
```

### Directory Responsibilities

#### `app/main.py`

FastAPI application entry point.

Responsibilities:

* Creates the FastAPI application.
* Registers routers.
* Configures application startup.
* Starts the APScheduler background job.

#### `app/core/`

Contains application-wide configuration and dependencies.

* `config.py` — loads environment variables and application settings.
* `client.py` — creates the Supabase client.
* `deps.py` — authentication and tenant-resolution dependencies.
* `pricing_constants.py` — token pricing constants.

#### `app/routers/`

Contains the HTTP/API layer.

Routers are responsible for:

* Request validation.
* HTTP responses.
* Authentication dependencies.
* Calling the appropriate service.
* Returning API results.

Business logic is kept in the service layer.

#### `app/services/`

Contains the application's business logic.

* `meter_service.py` — records usage events and handles idempotency.
* `quota_service.py` — checks API-call and token quotas.
* `pricing_service.py` — calculates AI-token costs.
* `stripe_service.py` — creates Stripe Checkout sessions.
* `rollup_service.py` — aggregates usage into monthly rollups.

#### `schema.sql`

Contains the PostgreSQL schema and seed data.

It creates:

* `tenants`
* `profiles`
* `plans`
* `subscriptions`
* `usage_events`
* `token_usage_details`
* `usage_rollups`
* `stripe_events`

It also seeds the Free and Pro plans.

#### `tests/`

Reserved for automated tests.

Currently, the project uses manual verification through curl/Postman requests and direct Supabase database checks.

## Prerequisites

* Python 3.11+
* A Supabase project
* A Stripe account in test mode
* Stripe CLI

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd LLM-Usage-Metering-Billing/backend
```

### 2. Create a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Supabase Setup

### 1. Create a Supabase Project

Create a project in Supabase.

### 2. Run the Database Schema

Open the Supabase SQL Editor and run:

```text
schema.sql
```

This creates the required tables and seeds the Free and Pro plans.

### 3. Get Supabase Credentials

From your Supabase project settings, obtain:

* Project URL
* Anon key
* Service role key

Add them to your `.env` file.

## Stripe Setup

Stripe is used only in **test mode**.

### 1. Create a Product

Create a product called:

```text
Pro
```

Create a recurring Price for the product and copy the Price ID.

### 2. Get the Stripe Secret Key

From the Stripe Dashboard, obtain your test-mode secret key.

### 3. Configure Stripe CLI

Authenticate the Stripe CLI:

```bash
stripe login
```

Then start webhook forwarding:

```bash
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
```

The CLI will display a webhook signing secret similar to:

```text
whsec_...
```

Add this value to your `.env` file.

## Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Configure:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

STRIPE_SECRET_KEY=your_stripe_test_secret_key
STRIPE_PRO_PRICE_ID=your_stripe_pro_price_id
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
```

## Running the Application

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Check the health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## Stripe Webhook Testing

Keep the application running in one terminal.

In a second terminal, run:

```bash
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
```

Then trigger a test event:

```bash
stripe trigger checkout.session.completed
```

The webhook endpoint verifies the Stripe signature before processing the event.

Duplicate Stripe events are detected using the Stripe event ID and are not processed twice.

## Plans

| Plan | API Calls / Month | AI Tokens / Month |
| ---- | ----------------: | ----------------: |
| Free |             1,000 |           100,000 |
| Pro  |            10,000 |         1,000,000 |

## API Reference

| Method | Endpoint                     | Authentication           | Purpose                                                         |
| ------ | ---------------------------- | ------------------------ | --------------------------------------------------------------- |
| GET    | `/health`                    | None                     | Liveness check                                                  |
| POST   | `/api/v1/auth/register`      | None                     | Register a user and provision a tenant with a Free subscription |
| POST   | `/api/v1/auth/login`         | None                     | Authenticate and return access/refresh tokens                   |
| POST   | `/api/v1/auth/refresh`       | None                     | Refresh an access token                                         |
| POST   | `/api/v1/auth/logout`        | None                     | Sign out                                                        |
| GET    | `/api/v1/auth/me`            | Bearer                   | Return the current user and tenant                              |
| GET    | `/api/v1/profile`            | Bearer                   | Get the current user's profile                                  |
| PATCH  | `/api/v1/profile`            | Bearer                   | Update the current user's profile                               |
| POST   | `/api/v1/generate`           | Bearer + Idempotency-Key | Record billable API or AI-token usage                           |
| GET    | `/api/v1/usage`              | Bearer                   | Return plan limits and usage                                    |
| POST   | `/api/v1/billing/checkout`   | Bearer                   | Create a Stripe Checkout session                                |
| GET    | `/api/v1/billing/success`    | None                     | Stripe Checkout redirect target                                 |
| POST   | `/api/v1/webhooks/stripe`    | Stripe signature         | Process Stripe webhook events                                   |
| POST   | `/api/v1/admin/usage/rollup` | None                     | Manually trigger the usage rollup job                           |

## Example: Recording API Usage

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Authorization: Bearer <token>" \
  -H "Idempotency-Key: <unique-uuid-per-request>" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"api_call"}'
```

## Example: Recording AI Token Usage

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Authorization: Bearer <token>" \
  -H "Idempotency-Key: <unique-uuid-per-request>" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"ai_tokens","input_tokens":2000,"cached_input_tokens":5000,"output_tokens":500,"reasoning_tokens":500}'
```

If the same request is retried with the same `Idempotency-Key`, the original usage event is returned instead of creating a second event.

This prevents:

```text
Request
   |
   +---- Attempt 1 ----> usage recorded
   |
   +---- Retry --------> existing event returned
```

rather than:

```text
Request
   |
   +---- Attempt 1 ----> usage recorded
   |
   +---- Retry --------> usage recorded again
```

## Quota Enforcement

Before recording usage, the system checks the tenant's current usage against the limits of the active plan.

```text
Incoming Request
       |
       v
Authenticate User
       |
       v
Resolve Tenant
       |
       v
Check Idempotency Key
       |
       v
Check Plan Quota
       |
       +------ Exceeded ------> 429 Too Many Requests
       |
       v
Calculate Cost
       |
       v
Record Usage Event
       |
       v
Return Result
```

The quota check handles boundary cases precisely.

For example, if a tenant has:

```text
Limit: 1,000 API calls
Current usage: 999
```

one additional API call is allowed.

If:

```text
Current usage: 1,000
```

the next API call is rejected.

## AI Token Pricing

AI usage supports:

* Input tokens
* Cached input tokens
* Output tokens
* Reasoning tokens

Reasoning tokens are billed at the output-token rate.

The resulting monetary cost is stored as **integer cents**, avoiding floating-point precision problems.

Conceptually:

```text
input cost
    +
cached input cost
    +
output cost
    +
reasoning cost
    =
total cost in cents
```

## Usage Rollups

Raw usage events are periodically aggregated into monthly usage summaries.

The rollup process groups usage by:

```text
tenant_id + event_type + billing period
```

The resulting data is stored in `usage_rollups` and is used by:

```text
GET /api/v1/usage
```

The application also exposes a manual rollup endpoint for verification:

```text
POST /api/v1/admin/usage/rollup
```

The background scheduler runs the rollup process every five minutes.

## Stripe Subscription Flow

The upgrade flow is:

```text
Free User
   |
   v
POST /api/v1/billing/checkout
   |
   v
Stripe Checkout
   |
   v
Customer completes payment
   |
   v
checkout.session.completed
   |
   v
Stripe Webhook
   |
   v
Verify Signature
   |
   v
Check Event ID
   |
   v
Update Subscription
   |
   v
Tenant becomes Pro
```

Downgrades are handled through:

```text
customer.subscription.deleted
```

which changes the tenant back to the Free plan.

`customer.subscription.updated` events are currently received and deduplicated but do not trigger additional subscription-state changes.

## Webhook Security

The Stripe webhook endpoint:

```text
POST /api/v1/webhooks/stripe
```

performs two important checks:

### 1. Signature Verification

The Stripe signature is verified using the configured webhook secret.

Invalid signatures are rejected.

### 2. Event Deduplication

Stripe event IDs are stored in:

```text
stripe_events
```

If the same event is received again, it is not processed a second time.

This protects subscription state from duplicate webhook deliveries.

## Multi-Tenant Isolation

The application does not accept a tenant ID from the client for authenticated operations.

Instead:

```text
JWT
 |
 v
User ID
 |
 v
Profile
 |
 v
Tenant ID
```

All usage, quotas, subscriptions, and rollups are then scoped using that tenant ID.

This prevents one tenant from requesting or modifying another tenant's usage data.

## Evidence

The project includes dedicated documentation for the capstone requirements:

* `EVIDENCE.md` — manual verification transcripts and database checks.
* `DESIGN.md` — architecture, data-model reasoning, and design decisions.
* `BUILDLOG.md` — development history, including AI-assisted development and bugs that were introduced and fixed.

## Limitations

* There is currently no automated test suite. Verification is performed through curl/Postman requests and direct Supabase database checks.
* `customer.subscription.updated` events are received and deduplicated but do not currently trigger subscription-state changes.
* The project does not implement invoicing, proration, or overage billing.
* Pricing constants in `pricing_constants.py` are illustrative placeholders and are not tied to a live AI provider's pricing.
* Stripe test-mode setup was used because Bangladesh is not among Stripe's directly supported account countries.

## Project Status

The backend currently demonstrates:

* Multi-tenant authentication
* JWT-based authorization
* Tenant isolation
* Idempotent usage metering
* API-call quotas
* AI-token quotas
* Token-based cost calculation
* Integer-cent cost storage
* Monthly usage rollups
* Stripe Checkout integration
* Stripe webhook signature verification
* Stripe event deduplication
* Free → Pro subscription synchronization
* Background usage aggregation

This project is intended as a backend engineering capstone demonstrating the core infrastructure required for usage-based SaaS billing.
