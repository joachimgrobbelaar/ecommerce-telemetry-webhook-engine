from pydantic import BaseModel, Field
from typing import Dict, Any

class WebhookIngestRequest(BaseModel):
    event_id: str = Field(..., description="Unique UUID for deduplication")
    topic: str = Field(..., description="E.g. orders/create, payments/succeeded")
    timestamp: int = Field(..., description="Epoch unix timestamp")
    data: Dict[str, Any] = Field(default_factory=dict)

class IngestResponse(BaseModel):
    event_id: str
    status: str
    message: str
