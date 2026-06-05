import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, to_date
from pyspark.sql.types import DoubleType

def main():
    print("🚀 Iniciando Motor PySpark Local...")

    # Leemos las variables de entorno inyectadas por Docker
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not bucket_name or not key_path:
        print("❌ Error: Faltan variables de entorno (GCS_BUCKET_NAME o GOOGLE_APPLICATION_CREDENTIALS)")
        return

    # ---------------------------------------------------------
    # 1. INICIALIZAR SPARK CON EL CONECTOR DE GOOGLE CLOUD
    # ---------------------------------------------------------
    spark = SparkSession.builder \
        .appName("BronzeToSilver") \
        .config("spark.jars", "/opt/spark/jars/gcs-connector-hadoop3-latest.jar") \
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
        .config("spark.hadoop.fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS") \
        .config("spark.hadoop.google.cloud.auth.service.account.enable", "true") \
        .config("spark.hadoop.google.cloud.auth.service.account.json.keyfile", key_path) \
        .getOrCreate()

    # Silenciar logs excesivos de Java en la terminal
    spark.sparkContext.setLogLevel("WARN")

    bronze_path = f"gs://{bucket_name}/bronze/telemetry/"
    silver_path = f"gs://{bucket_name}/silver/telemetry/"

    # ---------------------------------------------------------
    # 2. EXTRACCIÓN (LEER BRONCE)
    # ---------------------------------------------------------
    print(f"📖 Leyendo datos crudos desde {bronze_path}...")
    df_bronze = spark.read.format("json").load(f"{bronze_path}*/*.jsonl")
    print(f"✅ Se leyeron {df_bronze.count()} registros crudos.")

    # ---------------------------------------------------------
    # 3. TRANSFORMACIÓN (LIMPIEZA Y CASTEO)
    # ---------------------------------------------------------
    print("🧹 Limpiando y transformando datos...")
    df_silver = df_bronze \
        .withColumn("timestamp", to_timestamp(col("timestamp"))) \
        .withColumn("amount", col("amount").cast(DoubleType())) \
        .filter(col("user_id").isNotNull())
    
    # Extraemos la fecha del timestamp para crear la partición física
    df_silver_partitioned = df_silver.withColumn("dt", to_date(col("timestamp")))

    # ---------------------------------------------------------
    # 4. CARGA (ESCRIBIR PLATA)
    # ---------------------------------------------------------
    print(f"💾 Escribiendo en formato Parquet en {silver_path}...")
    df_silver_partitioned.write \
        .format("parquet") \
        .mode("append") \
        .partitionBy("dt") \
        .save(silver_path)

    print("🎯 ¡Éxito! Proceso Bronce a Plata finalizado.")
    spark.stop()

if __name__ == "__main__":
    main()
