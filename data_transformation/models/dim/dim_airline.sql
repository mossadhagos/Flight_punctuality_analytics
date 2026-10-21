with airlines as (

    select *
    from {{ ref('src_airlines') }}

),

deduplicated as (

    select
        reference_id,
        iata_code,
        icao_code,
        airline_name,
        callsign,
        country_region,
        comments,
        source_url,
        extracted_at_utc
    from airlines
    qualify row_number() over (
        partition by reference_id
        order by extracted_at_utc desc
    ) = 1

)

select
    reference_id as airline_id,
    iata_code,
    icao_code,
    airline_name,
    callsign,
    country_region,
    comments,
    source_url,
    extracted_at_utc
from deduplicated
where reference_id is not null