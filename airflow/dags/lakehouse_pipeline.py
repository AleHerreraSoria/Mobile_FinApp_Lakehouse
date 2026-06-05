from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

# 1. Argumentos por defecto del DAG
default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# 2. Definición del DAG
with DAG(
    'mobile_finapp_lakehouse_pipeline',
    default_args=default_args,
    description='Pipeline Medallón: Ingesta (Bronce) -> Transformación (Plata)',
    schedule_interval='@daily', # Se ejecutará una vez al día
    start_date=datetime(2026, 6, 4),
    catchup=False, # Evita que intente ejecutar días pasados de golpe
    tags=['finapp', 'lakehouse', 'medallion'],
) as dag:

    # Variables de entorno compartidas para los contenedores
    gcp_env_vars = {
        "GCS_BUCKET_NAME": "finapp-data-lake-dev-9923",
        "GOOGLE_APPLICATION_CREDENTIALS": "/keys/gcp-key.json",
        "MSYS_NO_PATHCONV": "1"
    }

    # Ruta absoluta de tu máquina local para inyectar la llave
    # DockerOperator necesita saber dónde está la llave en tu Windows/Host
    host_keys_path = "/d/Mobile_FinApp_Lakehouse/Mobile_FinApp_Lakehouse/keys"

    # ---------------------------------------------------------
    # TAREA 1: INGESTA A CAPA BRONCE
    # ---------------------------------------------------------
    ingest_to_bronze = DockerOperator(
        task_id='ingest_telemetry_to_bronze',
        image='finapp-ingestion:1.0',
        container_name='airflow_task_ingestion',
        api_version='auto',
        auto_remove='force', # Destruye el contenedor al terminar para liberar RAM
        mount_tmp_dir=False,
        environment=gcp_env_vars,
        mounts=[Mount(source=host_keys_path, target='/keys', type='bind', read_only=True)],
        network_mode='bridge',
        docker_url="unix://var/run/docker.sock", # El enchufe que mapeamos en el compose
    )

    # ---------------------------------------------------------
    # TAREA 2: TRANSFORMACIÓN A CAPA PLATA (SPARK)
    # ---------------------------------------------------------
    transform_to_silver = DockerOperator(
        task_id='transform_telemetry_to_silver_spark',
        image='finapp-spark:1.0',
        container_name='airflow_task_spark',
        api_version='auto',
        auto_remove='force',
        mount_tmp_dir=False,
        environment=gcp_env_vars,
        mounts=[Mount(source=host_keys_path, target='/keys', type='bind', read_only=True)],
        network_mode='bridge',
        docker_url="unix://var/run/docker.sock",
    )

    # 3. ORQUESTACIÓN (Definir el orden exacto)
    # El operador ">>" significa "se ejecuta antes que"
    ingest_to_bronze >> transform_to_silver