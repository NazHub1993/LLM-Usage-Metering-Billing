# Evidence

## Probe 1 — Idempotency
Same billable request sent twice with one Idempotency-Key → exactly one
usage_event; second response mirrors the first.

<img width="866" height="815" alt="Screenshot 2026-09-10 141541" src="https://github.com/user-attachments/assets/0abeb806-0a9e-4afc-a2ba-5900272bea0f" />


## Probe 2 — Quota boundary
Tenant driven to exact quota → boundary request allowed, next one rejected
with 429 and a clear message.

<img width="775" height="773" alt="Screenshot 2026-09-10 141727" src="https://github.com/user-attachments/assets/12a8ba82-0cc2-4fd9-9b4a-9705b3290e1a" />


## Probe 3 — Stripe Checkout → webhook → Free/Pro sync
Real Checkout completed in Stripe test mode; webhook received
checkout.session.completed, resolved tenant via client_reference_id,
updated subscriptions.plan_id to Pro:

<img width="1537" height="422" alt="Screenshot 2026-09-10 174314" src="https://github.com/user-attachments/assets/016e1fb3-fde6-43d3-976e-5a6a327cafc1" />


Confirmed via GET /usage immediately after:

   <img width="822" height="685" alt="image" src="https://github.com/user-attachments/assets/c3c67a4c-5586-41cd-9f53-a234bb605ed8" />


## Probe 4 — Webhook security
**Forged signature → 400, nothing changed:**

   <img width="1457" height="105" alt="Screenshot 2026-09-11 115317" src="https://github.com/user-attachments/assets/a3f3698a-5f8d-4a4d-8f90-973e46c371cb" />

**Real event replayed twice → processed once:**

   <img width="922" height="57" alt="Screenshot 2026-09-11 114546" src="https://github.com/user-attachments/assets/83dcfcc7-5976-4dca-96bd-20d0e6373298" />


## Probe 5 — Pricing correctness
Input: input_tokens=2000, cached_input_tokens=5000, output_tokens=500,
reasoning_tokens=500. Hand-calculated expected cost: $1.09 → 109 cents.

  <img width="192" height="455" alt="Screenshot 2026-09-10 171817" src="https://github.com/user-attachments/assets/928008fa-0508-4895-b37c-ee9288e93adc" />



Rollup correctly aggregates cost across events (post-fix):

   <img width="1483" height="285" alt="Screenshot 2026-09-11 143125" src="https://github.com/user-attachments/assets/320e34bb-c8b5-481f-b2ac-197698974196" />

GET /usage reflects these rollup values under "usage".
