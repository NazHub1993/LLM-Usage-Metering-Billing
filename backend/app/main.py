from fastapi import FastAPI 

from app.routers import auth
from app.routers import profile

app=FastAPI(title="LLM-Usage-Metering-Billing")

app.include_router(auth.router)
app.include_router(profile.router)


@app.get("/")
def get_health():
    return {"status": "ok"}