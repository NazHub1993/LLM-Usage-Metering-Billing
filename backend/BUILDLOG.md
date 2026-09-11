# Build Log — AI usage

Built with Claude as a step-by-step guide, one phase at a time. Logging
honestly per the brief's requirement — including the real bugs I introduced
and had to fix myself, not just what worked on the first try.

## Where AI helped
- Architecture: tenant/user separation, layer structure (router → service → DB)
- Explaining *why* idempotency keys must be checked before quota, not after
  (a subtlety I got wrong on my first attempt at /generate)
- Catching the parameter-order bug in pricing_service.calculate_cost_cents
  (output_tokens/reasoning_tokens swapped vs. the call site — same total in
  this case since both feed the same combined rate, but a real bug)
- Catching that rollup_service originally summed usage_events.quantity but
  never touched token_usage_details.cost_cents, so /usage always showed
  total_cost_cents: 0 for AI usage until fixed

## Where I made real mistakes (fixed after debugging)
- app/routers/generate.py: missing Header import, a NameError from
  referencing `event` instead of `result` in a return statement, and
  checking idempotency with `.single()` (which raises on zero rows) instead
  of a plain `.execute()` check on `.data`
- Used `event_type: "api-call"` (hyphen) as a default while
  quota_service compared against `"api_call"` (underscore) — silently fell
  through to the wrong quota bucket with no error
- POST /generate originally checked quota using the client-supplied
  `quantity` field even for ai_tokens requests, instead of the real sum of
  input/cached_input/output/reasoning tokens — meant a client could
  under-report usage and never trip the real token quota
- pricing_service.calculate_cost_cents used round(total, 6) instead of
  round(total) — stored cost_cents as a decimal (e.g. 108.75), violating
  the brief's "store money as integers" rule

## What I changed / verified myself
Every fix above was traced through by hand before accepting it — walked
through all execution paths (new request, quota-rejected, idempotent
replay) to confirm which variables are defined on each path, and
hand-calculated expected pricing totals to check against actual API
responses rather than trusting the code at a glance.

## Stripe test-mode account note
[Bangladesh is not among Stripe's directly-supported account countries.
Document here plainly how you set up your Stripe test account, since this
is exactly the kind of thing the brief wants logged honestly rather than
glossed over.]