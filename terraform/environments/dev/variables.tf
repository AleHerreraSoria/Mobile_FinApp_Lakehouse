variable "project_id" {
  description = "El ID del proyecto en GCP"
  type        = string
}

variable "region" {
  description = "Región de GCP"
  type        = string
  default     = "us-east1" # Usamos esta región por tener mejores costos/capacidad
}

variable "bucket_name" {
  description = "Nombre del bucket para el Data Lake"
  type        = string
}
