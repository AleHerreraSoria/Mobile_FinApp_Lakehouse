{{ config(materialized='table') }}

with raw_data as (
    select * from {{ source('gcp_lakehouse', 'ext_silver_telemetry') }}
)

select
    -- Generamos una llave primaria única para la transacción
    md5(concat(user_id, cast(timestamp as string), event_type)) as telemetry_key,
    user_id,
    event_type,
    amount,
    device_os,
    app_version,
    -- Campos de tiempo limpios casteados por Spark
    timestamp as event_timestamp,
    cast(timestamp as date) as event_date
from raw_data
where user_id is not null
