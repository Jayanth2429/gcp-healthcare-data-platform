from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from google.cloud import bigquery

from src.platform.events import decode_pubsub_push

app = FastAPI(title="CMS BigQuery Loader", version="1.0.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/pubsub")
async def pubsub(request: Request) -> dict[str, object]:
    project_id = os.environ.get("GCP_PROJECT_ID")
    dataset_name = os.environ.get("BQ_DATASET", "cms_platform")
    current_table = os.environ.get("BQ_CURRENT_TABLE", "hospital_general_information_current")
    audit_table = os.environ.get("BQ_AUDIT_TABLE", "ingestion_audit")
    if not project_id:
        raise HTTPException(status_code=500, detail="GCP_PROJECT_ID is missing")

    try:
        envelope = await request.json()
        payload = decode_pubsub_push(envelope)
        required = {"dataset_id", "bucket", "object_name", "sha256", "source_url", "ingested_at", "size_bytes"}
        missing = sorted(required.difference(payload))
        if missing:
            raise ValueError(f"snapshot event missing fields: {', '.join(missing)}")

        client = bigquery.Client(project=project_id)
        gcs_uri = f"gs://{payload['bucket']}/{payload['object_name']}"
        table_id = f"{project_id}.{dataset_name}.{current_table}"

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            autodetect=True,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
        load_job.result()
        destination = client.get_table(table_id)

        audit_id = f"{project_id}.{dataset_name}.{audit_table}"
        audit_row = {
            "loaded_at": datetime.now(timezone.utc).isoformat(),
            "source_dataset_id": payload["dataset_id"],
            "source_uri": gcs_uri,
            "source_sha256": payload["sha256"],
            "source_url": payload["source_url"],
            "source_ingested_at": payload["ingested_at"],
            "source_size_bytes": int(payload["size_bytes"]),
            "destination_table": table_id,
            "rows_loaded": int(destination.num_rows),
            "load_job_id": load_job.job_id,
        }
        errors = client.insert_rows_json(audit_id, [audit_row])
        if errors:
            raise RuntimeError(f"BigQuery audit insert failed: {errors}")

        return {
            "status": "loaded",
            "gcs_uri": gcs_uri,
            "destination_table": table_id,
            "rows_loaded": destination.num_rows,
            "load_job_id": load_job.job_id,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
