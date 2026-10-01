# Design Decisions

## Resolve CMS resources dynamically

Provider Data Catalog resources may rotate. The service resolves the active CSV URL from CMS metadata using the stable dataset identifier `xubh-q36u`.

## Persist before publish

The ingestor uploads the source to Cloud Storage before publishing the event. Downstream consumers therefore receive a durable object reference rather than depending on the upstream CMS URL remaining available.

## Immutable source objects

Timestamped object names retain source history and simplify audit/replay. GCS versioning adds another safeguard.

## Separate service identities

The ingestor needs write access to the raw bucket and publish access to Pub/Sub. The loader needs read access to the raw bucket plus BigQuery permissions. Keeping these identities separate reduces blast radius.

## BigQuery current table plus audit table

For this portfolio platform, the warehouse exposes a single current hospital table while the source archive preserves history. A production extension could create a slowly changing dimension or append-only historical table.
