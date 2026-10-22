import os 
import subprocess
import sys
from pathlib import Path

import dagster as dg
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

PROJECT_DIR = Path(__file__).resolve().parents[1]
DBT_DIR = PROJECT_DIR / "data_transformation"

dbt_project = DbtProject(
    project_dir=DBT_DIR,
    profiles_dir=os.getenv("DBT_PROFILES_DIR", str(DBT_DIR / ".dbt")),
)


def run_module(module: str) -> None:
    subprocess.run([sys.executable, "-m", module], cwd=PROJECT_DIR, check=True)


@dg.asset(group_name="ingestion")
def flight_snapshot() -> None:
    run_module("data_extract_load.dlt.collect_flights")


@dg.asset(group_name="ingestion")
def airline_snapshot() -> None:
    run_module("data_extract_load.dlt.collect_airlines")


@dg.asset(group_name="ingestion")
def airport_snapshot() -> None:
    run_module("data_extract_load.dlt.collect_airports")


@dg.multi_asset(
    specs=[
        dg.AssetSpec(["raw", "arrivals"], deps=[flight_snapshot], group_name="raw"),
        dg.AssetSpec(["raw", "departures"], deps=[flight_snapshot], group_name="raw"),
    ]
)
def load_flights():
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
    run_module("data_extract_load.dlt.load_references")
    for table in ("airlines", "airports"):
        yield dg.MaterializeResult(asset_key=["raw", table])


@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


daily_pipeline = dg.define_asset_job("daily_pipeline", selection=dg.AssetSelection.all())

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