from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.api.routes import router

app = FastAPI(
    title="Customer Support Ticket Triage API",
    description="Multi-Agent MoE Ticket Triage System with SLA Routing and Evaluation Harness",
    version="1.0.0"
)

app.include_router(router)

@app.get("/ui", include_in_schema=False)
def serve_dashboard():
    return FileResponse("app/static/index.html")