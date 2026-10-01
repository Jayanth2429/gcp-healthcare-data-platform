from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from google.cloud import pubsub_v1, storage

from src.platform.cms import (
    HOSPITAL_GENERAL_INFORMATION_ID,
    get_metadata,
    select_csv_distribution,
    download_csv,
)
from src.platform.events import SnapshotReadyEvent
from src.platform.hashing import sha256_file

app = FastAPI(title="CMS Snapshot Ingestor", version="1.0.0")


def _compact_timestamp(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest")
def ingest() -> dict[str, object]:
    project_id = os.environ.get("GCP_PROJECT_ID")
    bucket_name = os.environ.get("RAW_BUCKET")
    topic_name = os.environ.get("SNAPSHOT_TOPIC")
    if not project_id or not bucket_name or not topic_name:
        raise HTTPException(status_code=500, detail="required environment variables are missing")

    try:
        metadata = get_metadata(HOSPITAL_GENERAL_INFORMATION_ID)
        distribution = select_csv_distribution(metadata)
        source_url = str(distribution["downloadURL"])
        now = datetime.now(timezone.utc)
        stamp = _compact_timestamp(now)
        object_name = (
            "cms/hospital-general-information/"
            f"ingested_at={stamp}/hospital_general_information.csv"
        )

        with tempfile.TemporaryDirectory() as tmp:
            local_path = Path(tmp) / "hospital_general_information.csv"
            size_bytes = download_csv(source_url, local_path)
            checksum = sha256_file(local_path)

            storage_client = storage.Client(project=project_id)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            blob.metadata = {
                "cms_dataset_id": HOSPITAL_GENERAL_INFORMATION_ID,
                "sha256": checksum,
                "source_url": source_url,
            }
            blob.upload_from_filename(local_path, content_type="text/csv")

        event = SnapshotReadyEvent(
            dataset_id=HOSPITAL_GENERAL_INFORMATION_ID,
            bucket=bucket_name,
            object_name=object_name,
            sha256=checksum,
            source_url=source_url,
            ingested_at=now.isoformat(),
            size_bytes=size_bytes,
        )
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, topic_name)
        message_id = publisher.publish(topic_path, event.to_json_bytes()).result(timeout=30)

        return {
            "status": "published",
            "dataset_id": event.dataset_id,
            "gcs_uri": f"gs://{bucket_name}/{object_name}",
            "sha256": checksum,
            "size_bytes": size_bytes,
            "pubsub_message_id": message_id,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
