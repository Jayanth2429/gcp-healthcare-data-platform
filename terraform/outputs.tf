output "ingestor_url" {
  value = google_cloud_run_v2_service.ingestor.uri
}

output "loader_url" {
  value = google_cloud_run_v2_service.loader.uri
}

output "raw_bucket" {
  value = google_storage_bucket.raw.name
}

output "bigquery_dataset" {
  value = google_bigquery_dataset.platform.dataset_id
}

output "artifact_registry_repository" {
  value = google_artifact_registry_repository.images.name
}
