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
