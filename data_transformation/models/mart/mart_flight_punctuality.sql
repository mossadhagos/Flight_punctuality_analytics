with flights as (

    select
        arrival_key as flight_key,
        'Arrival' as direction,
        airport_key,
        airline_key,
        date_key,
        flight_number,
        origin_airport_iata as other_airport_iata,
        scheduled_at_utc,
        actual_at_utc,
        delay_minutes,
        is_delayed,
        is_cancelled,
        flight_status
    from {{ ref('fct_arrivals') }}
    where not is_deleted

    union all

    select
        departure_key,
        'Departure',
        airport_key,
        airline_key,
        date_key,
        flight_number,
        destination_airport_iata,
        scheduled_at_utc,
        actual_at_utc,
        delay_minutes,
        is_delayed,
        is_cancelled,
        flight_status
    from {{ ref('fct_departures') }}
    where not is_deleted

)

select
    f.flight_key,
    f.direction,
    f.flight_number,
    ap.iata_code as airport_iata,
    ap.airport_name,
    ap.city as airport_city,
    al.airline_name,
    al.iata_code as airline_iata,
    f.other_airport_iata,
    d.full_date as flight_date,
    d.year,
    d.month,
    d.month_name,
    d.weekday_number,
    d.weekday_name,
    f.scheduled_at_utc,
    f.actual_at_utc,
    f.delay_minutes,
    f.is_delayed,
    f.is_cancelled,
    f.flight_status
from flights as f
left join {{ ref('dim_airport') }} as ap
    on ap.airport_key = f.airport_key
left join {{ ref('dim_airline') }} as al
    on al.airline_key = f.airline_key
left join {{ ref('dim_date') }} as d
    on d.date_key = f.date_key