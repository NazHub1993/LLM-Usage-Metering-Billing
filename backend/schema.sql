-- schema.sql
-- Usage Metering & Billing Engine — full database schema
-- Run once, in order, against a fresh Supabase project (SQL Editor)

-- ============================================================
-- Phase 2: Core tenancy, auth, plans, subscriptions
-- ============================================================

create table tenants (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    created_at timestamptz default now()
);

create table profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    tenant_id uuid not null references tenants(id),
    name text,
    created_at timestamptz default now()
);

create table plans (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    api_call_limit int not null,
    ai_token_limit int not null,
    price_cents int not null default 0
);

create table subscriptions (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) unique,
    plan_id uuid not null references plans(id),
    status text not null default 'active',
    stripe_customer_id text,
    stripe_subscription_id text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table usage_events (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id),
    event_type text not null,
    quantity int not null,
    idempotency_key text not null unique,
    created_at timestamptz default now()
);

create table stripe_events (
    id text primary key,
    event_type text not null,
    processed_at timestamptz default now()
);

-- Seed the two plans this capstone uses
insert into plans (name, api_call_limit, ai_token_limit, price_cents) values
('Free', 1000, 100000, 0),
('Pro', 10000, 1000000, 2900);


-- ============================================================
-- Phase 5: AI token pricing breakdown
-- ============================================================

create table token_usage_details (
    id uuid primary key default gen_random_uuid(),
    usage_event_id uuid not null references usage_events(id),
    input_tokens int not null default 0,
    cached_input_tokens int not null default 0,
    output_tokens int not null default 0,
    reasoning_tokens int not null default 0,
    cost_cents int not null,
    created_at timestamptz default now()
);


-- ============================================================
-- Phase 8: Usage rollups + indexes
-- ============================================================

create table usage_rollups (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id),
    event_type text not null,
    total_quantity int not null default 0,
    total_cost_cents int not null default 0,
    period_start date not null,
    updated_at timestamptz default now(),
    unique(tenant_id, event_type, period_start)
);

create index idx_usage_events_tenant_type on usage_events(tenant_id, event_type);