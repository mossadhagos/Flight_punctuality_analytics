select
    reference_id,
    nullif(upper(trim(iata_code)), '') as iata_code,
    nullif(upper(trim(icao_code)), '') as icao_code,
    nullif(trim(airline_name), '') as airline_name,
    nullif(trim(callsign), '') as callsign,
    nullif(trim(country_region), '') as country_region,
    nullif(trim(comments), '') as comments,
    source_url,
    extracted_at_utc
from {{ source('raw', 'airlines') }}