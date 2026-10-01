from __future__ import annotations

import base64
import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SnapshotReadyEvent:
    dataset_id: str
    bucket: str
    object_name: str
    sha256: str
    source_url: str
    ingested_at: str
    size_bytes: int

    def to_json_bytes(self) -> bytes:
        return json.dumps(asdict(self), sort_keys=True).encode("utf-8")


def decode_pubsub_push(envelope: dict[str, Any]) -> dict[str, Any]:
    message = envelope.get("message")
    if not isinstance(message, dict):
        raise ValueError("missing Pub/Sub message")
    encoded = message.get("data")
    if not encoded:
        raise ValueError("missing Pub/Sub message data")
    raw = base64.b64decode(encoded)
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("Pub/Sub payload must be a JSON object")
    return payload
