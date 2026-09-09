from fastapi import FastAPI 

app=FastAPI(title="LLM-Usage-Metering-Billing")

@app.get("/health")
def get_health():
    return {"status": "ok"}