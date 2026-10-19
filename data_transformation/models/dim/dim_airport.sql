with src_airports as (
    select * from {{ ref('src_airports') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['iata_code']) }} as airport_key,
    iata_code,
    icao_code,
    airport_name,
    city,
    country
from src_airports