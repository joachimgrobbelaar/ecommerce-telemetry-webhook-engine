"""
High-Throughput Webhook Ingestion Service
Tailored for: Senior Backend Contract: High-Throughput E-Commerce Telemetry & Inventory Webhook Service
"""
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks
import hmac
import hashlib
from typing import Optional

from app.models import WebhookIngestRequest, IngestResponse

app = FastAPI(
    title="Webhook Telemetry Ingestion PoC",
    description="High-throughput webhook receiver with HMAC signature verification & deduplication",
    version="1.0.0"
)

SECRET_KEY = b"whsec_poc_test_secret_key"
SEEN_EVENTS = set()

def background_dispatch(event_id: str, topic: str):
    pass  # In production, dispatch to Redis task stream

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "webhook-ingest", "version": "1.0.0"}

@app.post("/webhooks/v1/ingest", response_model=IngestResponse)
async def ingest_webhook(
    request: Request,
    payload: WebhookIngestRequest,
    background_tasks: BackgroundTasks,
    x_signature: Optional[str] = Header(None)
):
    # Verify HMAC if provided
    raw_body = await request.body()
    if x_signature:
        expected = hmac.new(SECRET_KEY, raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, x_signature):
            raise HTTPException(status_code=403, detail="Invalid HMAC signature")

    # Deduplication
    if payload.event_id in SEEN_EVENTS:
        return IngestResponse(
            event_id=payload.event_id,
            status="duplicate_ignored",
            message="Event has already been processed"
        )
    
    SEEN_EVENTS.add(payload.event_id)
    background_tasks.add_task(background_dispatch, payload.event_id, payload.topic)
    
    return IngestResponse(
        event_id=payload.event_id,
        status="accepted",
        message="Event enqueued for asynchronous worker processing"
    )
