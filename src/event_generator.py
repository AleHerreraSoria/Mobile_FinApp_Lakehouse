import json
import os
import uuid
import random
import logging
from datetime import datetime, timedelta, timezone
from faker import Faker
from google.cloud import storage

# Configuración de logging nivel PRO (nada de 'print')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

fake = Faker()

def generate_event():
    # Viajamos al pasado: entre 0 y 90 días atrás, con una hora aleatoria
    dias_atras = random.randint(0, 90)
    minutos_atras = random.randint(0, 1440)
    fecha_aleatoria = datetime.now() - timedelta(days=dias_atras, minutes=minutos_atras)
    
    return {
        "user_id": f"user_{random.randint(1, 200)}",
        "event_type": random.choice(["login", "transfer", "check_balance", "error"]),
        "amount": round(random.uniform(5.0, 500.0), 2) if random.random() > 0.3 else 0.0,
        "device_os": random.choice(["Android", "iOS"]),
        "app_version": random.choice(["1.0", "1.1", "1.2"]),
        # Insertamos la fecha aleatoria en formato ISO
        "timestamp": fecha_aleatoria.isoformat()
    }
    
    # Si es una transferencia, agregamos datos financieros
    if event_type == 'transfer_initiated':
        event['amount'] = round(fake.random_number(digits=4) / 100, 2)
        event['currency'] = 'USD'
        
    return event

def upload_to_gcs(bucket_name, data, destination_blob_name):
    """Sube los datos crudos a Google Cloud Storage."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        
        blob.upload_from_string(data, content_type='application/jsonl')
        logger.info(f"Éxito: Archivo subido a gs://{bucket_name}/{destination_blob_name}")
    except Exception as e:
        logger.error(f"Error crítico subiendo a GCS: {e}")

def main():
    # En producción, NUNCA hardcodeamos variables, las leemos del entorno
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        logger.error("Falta la variable de entorno GCS_BUCKET_NAME.")
        return

    logger.info("Iniciando simulación de telemetría...")
    
    # Generamos un lote de 10000 eventos
    events = [generate_event() for _ in range(10000)]
    
    # Formato JSONL (estándar para Data Lakes)
    jsonl_data = "\n".join([json.dumps(event) for event in events])
    
    # Particionado Hive: bronze/telemetry/dt=YYYY-MM-DD/
    now = datetime.now(timezone.utc)
    date_partition = now.strftime('%Y-%m-%d')
    file_name = f"bronze/telemetry/dt={date_partition}/events_{now.strftime('%H%M%S')}.jsonl"
    
    upload_to_gcs(bucket_name, jsonl_data, file_name)

if __name__ == "__main__":
    main()