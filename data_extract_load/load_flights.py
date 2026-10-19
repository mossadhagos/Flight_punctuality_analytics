"""Validate and load the current three-day flight snapshot into Snowflake RAW."""

import argparse
import tomllib
from pathlib import Path

import dlt

from data_extract_load.api_client import recent_service_dates
from data_extract_load.collect_flights import (
    DIRECTIONS,
    read_snapshot,
    snapshot_path_for,
)

BASE_DIR = Path(__file__).resolve().parent

PRIMARY_KEY = [
    "flight_id",
    "scheduled_date",
    "airport_iata",
    "scheduled_at_utc",
]


def prepare_resources(snapshot: dict) -> list:
    """Separate arrivals/departures and validate their ingestion keys."""
    grouped = {direction: [] for direction in DIRECTIONS}
    seen = set()

    for original in snapshot["flights"]:
        row = dict(original)
        direction = row["flight_type"]

        if direction not in grouped:
            raise ValueError(f"Unexpected flight direction: {direction}")

        time_field = (
            "arrivalTime"
            if direction == "arrivals"
            else "departureTime"
        )

        row["scheduled_at_utc"] = (
            row.get(time_field) or {}
        ).get("scheduledUtc")

        if any(row.get(field) in (None, "") for field in PRIMARY_KEY):
            raise ValueError(
                f"Missing key field in {direction}: "
                f"{row.get('flight_id')}"
            )

        key = (direction, *(row[field] for field in PRIMARY_KEY))

        if key in seen:
            raise ValueError(
                f"Repeated ingestion key; no load started: {key}"
            )

        seen.add(key)
        grouped[direction].append(row)

    resources = []

    for direction, rows in grouped.items():
        print(f"Validated {direction}: {len(rows)} records")

        resources.append(
            dlt.resource(
                rows,
                name=direction,
                write_disposition="merge",
                primary_key=PRIMARY_KEY,
                max_table_nesting=0,
                columns={
                    "scheduled_date": {"data_type": "date"},
                    "scheduled_at_utc": {"data_type": "timestamp"},
                    "extracted_at_utc": {"data_type": "timestamp"},
                },
            )
        )

    return resources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without connecting to Snowflake",
    )
    args = parser.parse_args()

    dates = recent_service_dates()
    path = snapshot_path_for(dates)

    if not path.exists():
        raise SystemExit(
            "No snapshot for the current window. Run: "
            "uv run --locked python -m "
            "data_extract_load.collect_flights"
        )

    snapshot = read_snapshot(path, dates)

    print("Snapshot:", path.name)
    resources = prepare_resources(snapshot)

    if args.dry_run:
        print(
            "Validation passed. No API requests "
            "or Snowflake connection were made."
        )
        return

    secrets_path = BASE_DIR / ".dlt" / "secrets.toml"

    with secrets_path.open("rb") as file:
        credentials = tomllib.load(file)[
            "destination"
        ]["snowflake"]["credentials"]

    pipeline = dlt.pipeline(
        pipeline_name="swedavia_flights",
        pipelines_dir=str(BASE_DIR / ".dlt" / "pipelines"),
        destination=dlt.destinations.snowflake(
            credentials=credentials,
            staging_dataset_name_layout="%s_staging",
        ),
        dataset_name="raw",
    )

    print(pipeline.run(resources))


if __name__ == "__main__":
    main()