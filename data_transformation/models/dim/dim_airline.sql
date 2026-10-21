with flight_airlines as (

    select airline_icao_code, airline_iata_code, airline_name
    from {{ ref('src_arrivals') }}

    union

    select airline_icao_code, airline_iata_code, airline_name
    from {{ ref('src_departures') }}

),

wikipedia_airlines as (

    select
        icao_code,
        any_value(country_region) as country_region
    from {{ ref('src_airlines') }}
    where icao_code is not null
    group by icao_code
    having count(*) = 1

)

select
    {{ dbt_utils.generate_surrogate_key(['f.airline_icao_code']) }} as airline_key,
    f.airline_iata_code as iata_code,
    f.airline_icao_code as icao_code,
    f.airline_name,
    w.country_region
from flight_airlines as f
left join wikipedia_airlines as w
    on w.icao_code = f.airline_icao_code
