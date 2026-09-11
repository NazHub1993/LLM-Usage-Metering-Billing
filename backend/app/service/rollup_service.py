from datetime import date
from app.core.client import supabase


def run_usage_rollup():
    try:
        period_start = date.today().replace(day=1)

        # I am receiving all the events from usage_events table
        events = (supabase.table("usage_events")
                  .select("*,token_usage_details(cost_cents)").execute())
        totals = {}

        # Group usage by tenant + event_type
        for row in events.data:
            key = (row["tenant_id"], row["event_type"])
            if key not in totals:
                totals[key] = {"quantity": 0, "cost_cents": 0}
            totals[key]["quantity"] += row["quantity"]

            details = row.get("token_usage_details") or []
            for d in details:
                totals[key]["cost_cents"] += d["cost_cents"]

        # Store/update the monthly rollups
        for (tenant_id, event_type), sums in totals.items():
            supabase.table("usage_rollups").upsert({
                "tenant_id": tenant_id,
                "event_type": event_type,
                "total_quantity": sums["quantity"],
                "total_cost_cents": sums["cost_cents"],
                "period_start": period_start.isoformat(),
            }, on_conflict="tenant_id,event_type,period_start").execute()

        print(
            f"Rollup completed: "
            f"{len(totals)} tenant/event_type combinations updated"
        )

        return True

    except Exception as e:
        print(f"ROLLUP FAILED: {e}")
        return False
