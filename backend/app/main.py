from fastapi import FastAPI 

#Adding the scheduler code now
from apscheduler.schedulers.background import BackgroundScheduler
from app.service.rollup_service import run_usage_rollup
scheduler=BackgroundScheduler()



from app.routers import auth
from app.routers import profile
from app.routers import generate
from app.routers import billing
from app.routers import webhooks
from app.routers import admin
from app.routers import usage

app=FastAPI(title="LLM-Usage-Metering-Billing")


#================================rollup_scheduler
@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(
        run_usage_rollup,
        "interval",
        minutes=5,
        id="usage_rollup",
        replace_existing=True
    )
    scheduler.start()
    print("Usage rollup scheduler started!!")

@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown()
    print("Usage rollup scheduler stopped")

#=================================================================
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(generate.router)
app.include_router(billing.router)
app.include_router(webhooks.router)
app.include_router(admin.router)
app.include_router(usage.router)

@app.get("/")
def get_health():
    return {"status": "ok"}