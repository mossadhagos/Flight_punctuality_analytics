"""Dagster definitions: API snapshots -> Snowflake RAW (dlt) -> dbt models, run daily."""

import os
import subprocess
import sys
from pathlib import Path

import dagster as dg
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

PROJECT_DIR = Path(__file__).resolve().parents[1]
DBT_DIR = PROJECT_DIR / "data_transformation"

# DBT_PROFILES_DIR is set in Docker; locally we fall back to the project's .dbt folder.
dbt_project = DbtProject(
    project_dir=DBT_DIR,
    profiles_dir=os.getenv("DBT_PROFILES_DIR", str(DBT_DIR / ".dbt")),
)


def run_module(module: str) -> None:
    """Run an existing ingestion script as `python -m`; a non-zero exit fails the asset."""
    subprocess.run([sys.executable, "-m", module], cwd=PROJECT_DIR, check=True)


# --- Ingestion: fetch from the API and save local JSON snapshots ---


@dg.asset(group_name="ingestion")
def flight_snapshot() -> None:
    """Arrivals and departures for the last three UTC dates, saved as a JSON snapshot."""
    run_module("data_extract_load.dlt.collect_flights")


@dg.asset(group_name="ingestion")
def airline_snapshot() -> None:
    """Airline reference data, saved as a JSON snapshot."""
    run_module("data_extract_load.dlt.collect_airlines")


@dg.asset(group_name="ingestion")
def airport_snapshot() -> None:
    """Airport reference data, saved as a JSON snapshot."""
    run_module("data_extract_load.dlt.collect_airports")


# --- Load: push snapshots into Snowflake RAW with dlt ---
# One script writes two tables, so each loader is a multi_asset. The ["raw", <table>]
# keys match the dbt sources, which lets Dagster link them to the dbt models below.


@dg.multi_asset(
    specs=[
        dg.AssetSpec(["raw", "arrivals"], deps=[flight_snapshot], group_name="raw"),
        dg.AssetSpec(["raw", "departures"], deps=[flight_snapshot], group_name="raw"),
    ]
)
def load_flights():
    """Load the flight snapshot into RAW.arrivals and RAW.departures."""
    run_module("data_extract_load.dlt.load_flights")
    for table in ("arrivals", "departures"):
        yield dg.MaterializeResult(asset_key=["raw", table])


@dg.multi_asset(
    specs=[
        dg.AssetSpec(["raw", "airlines"], deps=[airline_snapshot], group_name="raw"),
        dg.AssetSpec(["raw", "airports"], deps=[airport_snapshot], group_name="raw"),
    ]
)
def load_references():
    """Load the airline and airport snapshots into RAW.airlines and RAW.airports."""
    run_module("data_extract_load.dlt.load_references")
    for table in ("airlines", "airports"):
        yield dg.MaterializeResult(asset_key=["raw", table])


# --- Transform: every dbt model becomes its own asset, read from manifest.json ---


@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    """Run `dbt build` (models + tests) for the selected models."""
    yield from dbt.cli(["build"], context=context).stream()


# --- Job and schedule: refresh everything once a day ---

daily_pipeline = dg.define_asset_job("daily_pipeline", selection=dg.AssetSelection.all())

# 06:00 every day, in UTC unless the Dagster instance sets another timezone.
daily_schedule = dg.ScheduleDefinition(job=daily_pipeline, cron_schedule="0 6 * * *")

defs = dg.Definitions(
    assets=[
        flight_snapshot,
        airline_snapshot,
        airport_snapshot,
        load_flights,
        load_references,
        dbt_models,
    ],
    jobs=[daily_pipeline],
    schedules=[daily_schedule],
    resources={"dbt": DbtCliResource(project_dir=dbt_project)},
)
