import base64
import json

import pytest

from src.platform.events import SnapshotReadyEvent, decode_pubsub_push


def test_snapshot_event_serialization_round_trip():
    event = SnapshotReadyEvent(
        dataset_id="xubh-q36u",
        bucket="raw-bucket",
        object_name="cms/snapshot.csv",
        sha256="abc123",
        source_url="https://example.com/data.csv",
        ingested_at="2026-10-01T17:00:00+00:00",
        size_bytes=123,
    )
    payload = json.loads(event.to_json_bytes())
    assert payload["dataset_id"] == "xubh-q36u"
    assert payload["size_bytes"] == 123


def test_decode_pubsub_push():
    raw = json.dumps({"bucket": "demo", "object_name": "file.csv"}).encode()
    envelope = {"message": {"data": base64.b64encode(raw).decode()}}
    payload = decode_pubsub_push(envelope)
    assert payload == {"bucket": "demo", "object_name": "file.csv"}


def test_decode_pubsub_push_rejects_missing_message():
    with pytest.raises(ValueError, match="missing Pub/Sub message"):
        decode_pubsub_push({})
