terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# 🌟 Injection de configurations fictives pour valider le plan en mode offline / CI/CD
provider "google" {
  project     = "terracosts-mock-project-id"
  region      = "europe-west1"
  zone        = "europe-west1-b"
  credentials = <<EOF
{
  "type": "service_account",
  "project_id": "terracosts-mock-project-id",
  "private_key_id": "mockkey1234567890",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC3V\n-----END PRIVATE KEY-----\n",
  "client_email": "mock-sa@terracosts-mock-project-id.iam.gserviceaccount.com",
  "client_id": "12345678901234567890",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mock-sa"
}
EOF
}

# Ton bucket GCP conforme avec ses labels
resource "google_storage_bucket" "gcp_test_bucket" {
  name          = "terracosts-gcp-backend-test-bucket"
  location      = "EU"
  force_destroy = true

  labels = {
    environment = "production"
    project     = "core-backend"
    owner       = "nadset-saas"
  }
}
# TerraCosts Gating Full Matrix Test
# Triggering FinOps Gating Review
# Manual dispatch activation run
