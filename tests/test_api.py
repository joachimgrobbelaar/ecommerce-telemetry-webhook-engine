import pytest
import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from app.main import app, SECRET_KEY

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_webhook_ingest_and_deduplication():
    payload = {
        "event_id": "evt_test_unique_101",
        "topic": "orders.created",
        "timestamp": 1729000000,
        "data": {"order_id": 9942, "amount": 149.99}
    }
    raw = json.dumps(payload).encode("utf-8")
    sig = hmac.new(SECRET_KEY, raw, hashlib.sha256).hexdigest()

    # First ingest: accepted
    res1 = client.post(
        "/webhooks/v1/ingest",
        data=raw,
        headers={"Content-Type": "application/json", "X-Signature": sig}
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "accepted"

    # Second ingest: duplicate ignored
    res2 = client.post(
        "/webhooks/v1/ingest",
        data=raw,
        headers={"Content-Type": "application/json", "X-Signature": sig}
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "duplicate_ignored"

def test_invalid_hmac_rejected():
    payload = {
        "event_id": "evt_bad_sig_202",
        "topic": "payment.failed",
        "timestamp": 1729000000,
        "data": {}
    }
    res = client.post(
        "/webhooks/v1/ingest",
        json=payload,
        headers={"X-Signature": "invalid_hex_digest_value"}
    )
    assert res.status_code == 403
