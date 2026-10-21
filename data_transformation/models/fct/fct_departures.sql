with departures as (

    select
        *,
        cast(
            datediff('second', scheduled_at_utc, actual_at_utc) / 60
            as decimal(10, 2)
        ) as delay_minutes
    from {{ ref('src_departures') }}

)

select
    {{ dbt_utils.generate_surrogate_key(['flight_id', 'airport_iata', 'scheduled_at_utc']) }} as departure_key,
    {{ dbt_utils.generate_surrogate_key(['airport_iata']) }} as airport_key,
    {{ dbt_utils.generate_surrogate_key(['airline_icao_code']) }} as airline_key,
    cast(to_char(scheduled_date, 'YYYYMMDD') as integer) as date_key,
    flight_id as flight_number,
    flight_departure_date_utc,
    destination_airport_iata,
    scheduled_at_utc,
    actual_at_utc,
    delay_minutes,
    delay_minutes > 15 as is_delayed,
    flight_status,
    coalesce(flight_status = 'CAN', false) as is_cancelled,
    is_deleted
from departures
