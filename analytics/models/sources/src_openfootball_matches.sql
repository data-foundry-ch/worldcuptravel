{{ config(materialized='view') }}

select *
from read_parquet('{{ env_var("MATCHES_PARQUET_PATH") }}')
