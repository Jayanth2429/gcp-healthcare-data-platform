# Architecture

## Data flow

1. **Cloud Scheduler** invokes the ingestor Cloud Run service on a schedule using OIDC.
2. **Ingestor** resolves the active CMS CSV from the stable Provider Data Catalog dataset identifier.
3. The source CSV is downloaded, hashed, and uploaded to a timestamped path in **Cloud Storage**.
4. Ingestor publishes a **snapshot-ready** message to Pub/Sub.
5. Pub/Sub pushes the event to the loader Cloud Run service using an authenticated OIDC request.
6. **Loader** performs a BigQuery load job from GCS into the current hospital table.
7. Loader appends operational metadata to the BigQuery ingestion audit table.

## Zones

### Raw zone

Cloud Storage is the immutable system of record for every source snapshot. Object versioning is also enabled to protect against accidental replacement.

### Current warehouse table

The BigQuery current table is refreshed with `WRITE_TRUNCATE`. This keeps the consumption interface simple while source history remains preserved in GCS.

### Audit layer

Every successful warehouse load records the input URI, source hash, source dataset ID, source timestamp, source size, destination table, row count, and BigQuery job ID.

## Failure boundaries

The ingestion and load stages are deliberately separated. A temporary BigQuery issue does not require redownloading CMS data; Pub/Sub can retry the loader using the already persisted GCS snapshot.
