locals {
  services = toset([
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "cloudbuild.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
    "cloudscheduler.googleapis.com",
  ])
}

resource "google_project_service" "required" {
  for_each           = local.services
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "images" {
  depends_on    = [google_project_service.required]
  location      = var.region
  repository_id = "data-platform"
  description   = "Cloud data platform service images"
  format        = "DOCKER"
}

resource "google_storage_bucket" "raw" {
  depends_on                  = [google_project_service.required]
  name                        = var.raw_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

resource "google_pubsub_topic" "snapshot_ready" {
  depends_on = [google_project_service.required]
  name       = "cms-snapshot-ready"
}

resource "google_bigquery_dataset" "platform" {
  depends_on = [google_project_service.required]
  dataset_id = "cms_platform"
  location   = "US"
  description = "CMS public hospital data platform"
}

resource "google_bigquery_table" "audit" {
  dataset_id = google_bigquery_dataset.platform.dataset_id
  table_id   = "ingestion_audit"

  schema = jsonencode([
    { name = "loaded_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "source_dataset_id", type = "STRING", mode = "REQUIRED" },
    { name = "source_uri", type = "STRING", mode = "REQUIRED" },
    { name = "source_sha256", type = "STRING", mode = "REQUIRED" },
    { name = "source_url", type = "STRING", mode = "REQUIRED" },
    { name = "source_ingested_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "source_size_bytes", type = "INTEGER", mode = "REQUIRED" },
    { name = "destination_table", type = "STRING", mode = "REQUIRED" },
    { name = "rows_loaded", type = "INTEGER", mode = "REQUIRED" },
    { name = "load_job_id", type = "STRING", mode = "REQUIRED" }
  ])
}

resource "google_service_account" "ingestor" {
  account_id   = "cms-ingestor"
  display_name = "CMS Ingestor"
}

resource "google_service_account" "loader" {
  account_id   = "cms-loader"
  display_name = "CMS Loader"
}

resource "google_service_account" "scheduler" {
  account_id   = "cms-scheduler"
  display_name = "CMS Scheduler"
}

resource "google_service_account" "pubsub_push" {
  account_id   = "cms-pubsub-push"
  display_name = "CMS PubSub Push"
}

resource "google_storage_bucket_iam_member" "ingestor_object_admin" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.ingestor.email}"
}

resource "google_storage_bucket_iam_member" "loader_object_viewer" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.loader.email}"
}

resource "google_pubsub_topic_iam_member" "ingestor_publisher" {
  topic  = google_pubsub_topic.snapshot_ready.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.ingestor.email}"
}

resource "google_project_iam_member" "loader_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.loader.email}"
}

resource "google_bigquery_dataset_iam_member" "loader_bq_editor" {
  dataset_id = google_bigquery_dataset.platform.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.loader.email}"
}

resource "google_cloud_run_v2_service" "ingestor" {
  depends_on = [google_project_service.required]
  name       = "cms-ingestor"
  location   = var.region

  template {
    service_account = google_service_account.ingestor.email
    containers {
      image = var.ingestor_image
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "RAW_BUCKET"
        value = google_storage_bucket.raw.name
      }
      env {
        name  = "SNAPSHOT_TOPIC"
        value = google_pubsub_topic.snapshot_ready.name
      }
    }
  }
}

resource "google_cloud_run_v2_service" "loader" {
  depends_on = [google_project_service.required]
  name       = "cms-loader"
  location   = var.region

  template {
    service_account = google_service_account.loader.email
    containers {
      image = var.loader_image
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "BQ_DATASET"
        value = google_bigquery_dataset.platform.dataset_id
      }
      env {
        name  = "BQ_CURRENT_TABLE"
        value = "hospital_general_information_current"
      }
      env {
        name  = "BQ_AUDIT_TABLE"
        value = google_bigquery_table.audit.table_id
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "scheduler_invoker" {
  name     = google_cloud_run_v2_service.ingestor.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_run_v2_service_iam_member" "pubsub_loader_invoker" {
  name     = google_cloud_run_v2_service.loader.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.pubsub_push.email}"
}

resource "google_pubsub_subscription" "loader_push" {
  name  = "cms-loader-push"
  topic = google_pubsub_topic.snapshot_ready.name

  ack_deadline_seconds = 600

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.loader.uri}/pubsub"
    oidc_token {
      service_account_email = google_service_account.pubsub_push.email
      audience              = google_cloud_run_v2_service.loader.uri
    }
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

resource "google_cloud_scheduler_job" "weekly_ingest" {
  depends_on = [google_project_service.required]
  name       = "cms-weekly-ingest"
  region     = var.region
  schedule   = var.schedule
  time_zone  = "America/Chicago"

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.ingestor.uri}/ingest"
    oidc_token {
      service_account_email = google_service_account.scheduler.email
      audience              = google_cloud_run_v2_service.ingestor.uri
    }
  }
}
