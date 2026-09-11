from fastapi import FastAPI 

from app.routers import auth
from app.routers import profile
from app.routers import generate
from app.routers import billing
from app.routers import webhooks

app=FastAPI(title="LLM-Usage-Metering-Billing")

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(generate.router)
app.include_router(billing.router)
app.include_router(webhooks.router)


@app.get("/")
def get_health():
    return {"status": "ok"}