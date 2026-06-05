# 1. GCS Bucket (Data Lake: Capas Bronce y Plata)
resource "google_storage_bucket" "data_lake" {
  name                        = var.bucket_name
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# 2. BigQuery Dataset (Data Warehouse: Capa Oro para dbt)
resource "google_bigquery_dataset" "gold_layer" {
  dataset_id                      = "finapp_gold_layer"
  friendly_name                   = "FinApp Gold Layer"
  description                     = "Capa Oro gestionada por dbt"
  location                        = var.region
  delete_contents_on_destroy      = true
  default_table_expiration_ms     = 5184000000 # 60 días para tablas
  default_partition_expiration_ms = 5184000000 # 60 días para particiones
}

# 3. BigQuery External Table (Puente entre Plata y Oro)
resource "google_bigquery_table" "ext_silver_telemetry" {
  dataset_id = google_bigquery_dataset.gold_layer.dataset_id
  table_id   = "ext_silver_telemetry"
  project    = var.project_id
  deletion_protection = false # Falso para permitir destruir el entorno Dev fácilmente

  external_data_configuration {
    autodetect    = true
    source_format = "PARQUET"
    
    # Apuntamos a la carpeta Silver (el asterisco lee todos los archivos y particiones)
    source_uris = [
      "gs://${google_storage_bucket.data_lake.name}/silver/telemetry/*"
    ]
  }
}
