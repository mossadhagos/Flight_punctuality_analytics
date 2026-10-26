# Flight punctuality analytics

This project analyses delayed arrivals and departures at ten Swedish airports.
The Streamlit dashboard lets users compare punctuality by airport, airline,
date and flight direction.

## Data flow

```text
Swedavia FlightInfo API + Wikipedia airline and airport references
    -> Python collectors and saved JSON snapshots
    -> dlt -> Snowflake FLIGHT_DB.RAW
    -> dbt ephemeral preparation models (models/src)
    -> dimensions and facts in FLIGHT_DB.DIMENSIONAL
    -> mart_flight_punctuality in FLIGHT_DB.MARTS
    -> Streamlit dashboard

Dagster coordinates collection, loading and dbt builds.
```

Flights are collected for today and the previous two UTC dates, for ARN, BMA,
GOT, MMX, LLA, UME, OSD, VBY, RNB and KRN. Loads merge matching keys and retain
older records, so the dashboard can cover more than the latest three days.

## Local setup

Prerequisites: Git, uv, Python 3.12 or newer, a Swedavia FlightInfo API key and
access to the group's shared Snowflake account.

Clone the repository, or use your existing checkout. Run all commands below
from the repository root:

```bash
git clone https://github.com/mossadhagos/Flight_punctuality_analytics.git
cd Flight_punctuality_analytics
uv sync --locked
```

Snowflake setup scripts are under `snowflake_setup/`. The local workflow assumes
the shared `FLIGHT_DB` database, `FLIGHT_WH` warehouse and required roles/grants
already exist. Loading needs access to both `RAW` and the dlt merge workspace
`RAW_STAGING`; dbt needs read access to RAW and write access to `STAGING`,
`DIMENSIONAL` and `MARTS`. The current setup scripts do not create or grant access
to `RAW_STAGING`, so confirm that access with the account administrator.

### Private connection files

The examples below contain placeholders. Replace them locally with your own
credentials and use roles assigned to your user. Keep existing working private
files if you already configured the project. These four files are ignored by Git;
do not add credentials to the README or commit the private files.

Create the directories if needed:

```bash
mkdir -p data_extract_load/.dlt data_transformation/.dbt .streamlit
```

**1. `.env` at the repository root:**

```dotenv
SWEDAVIA_API_KEY=YOUR_SWEDAVIA_API_KEY
```

**2. `data_extract_load/.dlt/secrets.toml` for loading:**

```toml
[destination.snowflake.credentials]
host = "YOUR_SNOWFLAKE_ACCOUNT_IDENTIFIER"
username = "YOUR_SNOWFLAKE_USER"
password = "YOUR_SNOWFLAKE_PASSWORD"
database = "FLIGHT_DB"
warehouse = "FLIGHT_WH"
role = "DLT_ROLE"
```

**3. `data_transformation/.dbt/profiles.yml` for dbt:**

```yaml
dbt_snowflake:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "YOUR_SNOWFLAKE_ACCOUNT_IDENTIFIER"
      user: "YOUR_SNOWFLAKE_USER"
      password: "YOUR_SNOWFLAKE_PASSWORD"
      role: DBT_ROLE
      warehouse: FLIGHT_WH
      database: FLIGHT_DB
      schema: STAGING
      threads: 2
```

**4. `.streamlit/secrets.toml` for the dashboard:**

```toml
[connections.snowflake]
account = "YOUR_SNOWFLAKE_ACCOUNT_IDENTIFIER"
user = "YOUR_SNOWFLAKE_USER"
password = "YOUR_SNOWFLAKE_PASSWORD"
role = "REPORTER_ROLE"
warehouse = "FLIGHT_WH"
database = "FLIGHT_DB"
schema = "MARTS"
```

Use the account identifier without `https://` or a browser URL. The dashboard's
read-only `REPORTER_ROLE` needs SELECT access to MARTS. Its connection must use
`MARTS` because the dashboard queries `mart_flight_punctuality` without a schema
prefix. If `SNOWFLAKE_*` environment variables are set in the launching terminal,
the dashboard uses that connection configuration instead of this local template.

## Ingestion

Collect today's and the previous two UTC dates, then collect Wikipedia references:

```bash
uv run --locked python -m data_extract_load.dlt.collect_flights
uv run --locked python -m data_extract_load.dlt.collect_airlines
uv run --locked python -m data_extract_load.dlt.collect_airports
```

Snapshots stay in `data_extract_load/data/` and are ignored by Git.
The flight collector reuses a snapshot only for the current three-day window.
The Wikipedia collectors reuse their saved reference snapshots.

Validate the snapshots locally, then load them into Snowflake RAW:

```bash
uv run --locked python -m data_extract_load.dlt.load_flights --dry-run
uv run --locked python -m data_extract_load.dlt.load_references --dry-run
uv run --locked python -m data_extract_load.dlt.load_flights
uv run --locked python -m data_extract_load.dlt.load_references
```

The target tables are `FLIGHT_DB.RAW.ARRIVALS`, `DEPARTURES`, `AIRLINES`
and `AIRPORTS`. Both loaders merge matching keys. Local pipeline state remains
in the ignored `data_extract_load/.dlt/pipelines/` directory.

Run the API-client tests:

```bash
uv run --locked python -m pytest data_extract_load/dlt/test_api_client.py -q
```

## dbt transformations

The dbt structure follows the [course modeling example](https://github.com/AIgineerAB/modern-data-stack-course/tree/main/10_dbt_modeling/dbt_code).

Use `models/src` for ephemeral preparation models, `models/dim` for dimensions,
`models/fct` for facts, and `models/mart` for reporting models. Dimensions and
facts target `FLIGHT_DB.DIMENSIONAL`; reporting models target `FLIGHT_DB.MARTS`.
The course uses WAREHOUSE for dimensions/facts; this project uses the group's
existing DIMENSIONAL schema. The course schema macro uses shared schema names.

Ephemeral models are compiled into the queries of their dependants. They do not
create standalone tables or views. Previously created `STG_*` views are not managed
by the renamed models.

Install the course-pinned dbt_utils package and check the connection:

```bash
uv run --locked dbt deps --project-dir data_transformation --profiles-dir data_transformation/.dbt
uv run --locked dbt debug --project-dir data_transformation --profiles-dir data_transformation/.dbt
```

After loading RAW data, build all models and run their data tests:

```bash
uv run --locked dbt build --project-dir data_transformation --profiles-dir data_transformation/.dbt
```

This builds `dim_airport`, `dim_airline`, `dim_date`, `fct_arrivals`,
`fct_departures` and `mart_flight_punctuality`. Model tests are defined in
`data_transformation/models/schema.yml`. The dimensional diagram is defined in
`data_transformation/flight_model.dbml`; open it in dbdiagram to view relationships.

To test only the four preparation models:

```bash
uv run --locked dbt test --project-dir data_transformation --profiles-dir data_transformation/.dbt --select src_airports src_airlines src_arrivals src_departures
```

## Streamlit dashboard

After a successful dbt build, start the dashboard from the repository root:

```bash
uv run --locked streamlit run dashboard/app.py
```

Open http://localhost:8501. Use Home for headline metrics, Data for tables and
Charts for comparisons. Sidebar filters select dates, direction, airports and
airlines. A flight is delayed when its actual time is more than 15 minutes after
its scheduled time. Flights with unknown actual times are excluded from delay
rates; the total flight count can therefore be higher than the count used in
delay summaries. The mart excludes deleted records.

Query results are cached for up to ten minutes. After a new pipeline run, allow
the cache to expire or stop and restart Streamlit to display updated data.

## Dagster orchestration

Complete the connection setup, `dbt deps` and initial dbt build above first.
Dagster reads the generated manifest at `data_transformation/target/manifest.json`.

In a separate terminal, run this from the repository root:

```bash
uv run --locked dagster dev -f orchestration/definitions.py -p 3000
```

Open http://localhost:3000, select **Jobs -> daily_pipeline**, then choose
**Materialize all**. This collects snapshots, loads the four RAW tables and runs
the dbt build with its tests. Check **Runs** for success and the asset graph for
materializations and test results. Starting the webserver alone does not run the
pipeline.

The job has a daily schedule at **06:00 UTC**. Enable it in Automation only when
you want automatic runs. Local scheduled execution requires the Dagster processes
and the computer to remain running. Keep both terminals open while demonstrating
Dagster and Streamlit; use Ctrl+C in each terminal to stop them.
