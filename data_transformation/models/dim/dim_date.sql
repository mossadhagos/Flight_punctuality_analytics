with date_spine as (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2026-01-01' as date)",
        end_date="cast('2028-01-01' as date)"
    ) }}

)

select
    cast(to_char(date_day, 'YYYYMMDD') as integer) as date_key,
    cast(date_day as date) as full_date,
    year(date_day) as year,
    month(date_day) as month,
    monthname(date_day) as month_name,
    day(date_day) as day_of_month,
    dayofweekiso(date_day) as weekday_number,
    dayname(date_day) as weekday_name
from date_spine
