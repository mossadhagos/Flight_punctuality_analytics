# Flight punctuality analytics

## Ingestion

Run commands from the repository root. Install dependencies with `uv sync --locked`.

Create the ignored `.env` file with `SWEDAVIA_API_KEY` and the ignored
`data_extract_load/.dlt/secrets.toml` file with a
`[destination.snowflake.credentials]` section containing `host`, `username`,
`password`, `database`, `warehouse` and `role`. The group loading role is
`DLT_ROLE`; the database is `FLIGHT_DB` and warehouse is `FLIGHT_WH`.
The role needs access to the existing RAW and RAW_STAGING schemas.

Collect today's and the previous two UTC dates, then collect Wikipedia references:

    uv run --locked python -m data_extract_load.dlt.collect_flights
    uv run --locked python -m data_extract_load.dlt.collect_airlines
    uv run --locked python -m data_extract_load.dlt.collect_airports

Snapshots stay in `data_extract_load/data/` and are ignored by Git.
The flight collector reuses a snapshot only for the current three-day window.
The Wikipedia collectors reuse their saved reference snapshots.

Validate the snapshots locally, then load them into Snowflake RAW:

    uv run --locked python -m data_extract_load.dlt.load_flights --dry-run
    uv run --locked python -m data_extract_load.dlt.load_references --dry-run
    uv run --locked python -m data_extract_load.dlt.load_flights
    uv run --locked python -m data_extract_load.dlt.load_references

The target tables are `FLIGHT_DB.RAW.ARRIVALS`, `DEPARTURES`, `AIRLINES`
and `AIRPORTS`. Both loaders merge matching keys. Local pipeline state remains
in the ignored `data_extract_load/.dlt/pipelines/` directory.

Run the API-client tests:

    uv run --locked python -m pytest data_extract_load/dlt/test_api_client.py -q

## dbt transformations

The dbt structure follows the course modeling example:
https://github.com/AIgineerAB/modern-data-stack-course/tree/main/10_dbt_modeling/dbt_code

Use models/src for ephemeral preparation models, models/dim for dimensions,
models/fct for facts, and models/mart for reporting models. Dimensions and
facts target FLIGHT_DB.DIMENSIONAL; reporting models target FLIGHT_DB.MARTS.
The course uses WAREHOUSE for dimensions/facts; this project uses the group's
existing DIMENSIONAL schema. The course schema macro uses shared schema names.

Keep connection credentials in the ignored data_transformation/.dbt/profiles.yml.
Install the course-pinned dbt_utils package:

    uv run --locked dbt deps --project-dir data_transformation --profiles-dir data_transformation/.dbt

Validate the four preparation models:

    uv run --locked dbt test --project-dir data_transformation --profiles-dir data_transformation/.dbt --select src_airports src_airlines src_arrivals src_departures

Ephemeral models are compiled into the queries of their dependants. They do not
create standalone tables or views. Previously created STG_* views are not managed
by the renamed models; this change does not drop them or alter RAW tables.
