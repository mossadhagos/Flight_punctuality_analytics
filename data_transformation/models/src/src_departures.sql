with extracted as (

    select
        flight_id,
        scheduled_date,
        upper(trim(airport_iata)) as airport_iata,

        to_date(
            left(
                flight_leg_identifier:flightDepartureDateUtc::varchar,
                10
            )
        ) as flight_departure_date_utc,

        nullif(
            upper(trim(
                flight_leg_identifier:departureAirportIata::varchar
            )),
            ''
        ) as origin_airport_iata,

        nullif(
            upper(trim(
                flight_leg_identifier:arrivalAirportIata::varchar
            )),
            ''
        ) as destination_airport_iata,

        nullif(
            upper(trim(airline_operator:iata::varchar)),
            ''
        ) as airline_iata_code,

        nullif(
            upper(trim(airline_operator:icao::varchar)),
            ''
        ) as airline_icao_code,

        nullif(
            trim(airline_operator:name::varchar),
            ''
        ) as airline_name,

        convert_timezone(
            'UTC',
            to_timestamp_tz(departure_time:scheduledUtc::varchar)
        )::timestamp_ntz as scheduled_at_utc,

        convert_timezone(
            'UTC',
            to_timestamp_tz(departure_time:actualUtc::varchar)
        )::timestamp_ntz as actual_at_utc,

        nullif(
            upper(trim(
                location_and_status:flightLegStatus::varchar
            )),
            ''
        ) as flight_status,

        extracted_at_utc

    from {{ source('raw', 'departures') }}

)

select
    *,
    coalesce(flight_status = 'DEL', false) as is_deleted
from extracted