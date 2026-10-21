select
    nullif(upper(trim(iata_code)), '') as iata_code,
    nullif(upper(trim(icao_code)), '') as icao_code,
    nullif(trim(airport_name), '') as airport_name,
    nullif(trim(city), '') as city,
    nullif(trim(country), '') as country,
    extracted_at_utc
from {{ source('raw', 'airports') }}