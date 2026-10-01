variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "raw_bucket_name" {
  description = "Globally unique raw bucket name"
  type        = string
}

variable "ingestor_image" {
  description = "Artifact Registry image URI for the ingestor"
  type        = string
}

variable "loader_image" {
  description = "Artifact Registry image URI for the loader"
  type        = string
}

variable "schedule" {
  description = "Cloud Scheduler cron expression"
  type        = string
  default     = "0 6 * * 1"
}
