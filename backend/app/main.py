from fastapi import FastAPI 

from app.routers import auth

app=FastAPI(title="LLM-Usage-Metering-Billing")

app.include_router(auth.router)


@app.get("/")
def get_health():
    return {"status": "ok"}