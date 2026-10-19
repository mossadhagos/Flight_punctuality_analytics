"""Load saved Wikipedia airline and airport references into Snowflake RAW."""

import argparse
import json
import tomllib
from datetime import datetime
from pathlib import Path

import dlt

from data_extract_load.dlt.collect_airports import validate_airports

BASE_DIR = Path(__file__).resolve().parents[1]


def prepare_resources() -> list:
    """Validate both snapshots before connecting to Snowflake."""
    resources = []

    for name, primary_key in (
        ("airlines", "reference_id"),
        ("airports", "iata_code"),
    ):
        path = BASE_DIR / "data" / f"wikipedia_{name}.json"

        if not path.exists():
            raise ValueError(
                f"Missing snapshot. "
                f"Run the collect_{name} module first."
            )

        snapshot = json.loads(
            path.read_text(encoding="utf-8")
        )
        records = snapshot[name]

        if not isinstance(records, list) or not records:
            raise ValueError(
                f"Empty or invalid {name} snapshot."
            )

        extracted_at = datetime.fromisoformat(
            snapshot["extracted_at_utc"]
        )

        if extracted_at.tzinfo is None:
            raise ValueError(
                f"Missing extraction timezone in {name} snapshot."
            )

        keys = []

        for row in records:
            if not isinstance(row, dict):
                raise ValueError(
                    f"Invalid record in {name} snapshot."
                )

            key = row.get(primary_key)

            if not isinstance(key, str) or not key.strip():
                raise ValueError(
                    f"Missing {primary_key} in {name} snapshot."
                )

            keys.append(key)

        if len(set(keys)) != len(keys):
            raise ValueError(
                f"Repeated {primary_key} in {name} snapshot."
            )

        if name == "airports":
            validate_airports(records)

        rows = [
            {
                **row,
                "extracted_at_utc": extracted_at,
            }
            for row in records
        ]

        resources.append(
            dlt.resource(
                rows,
                name=name,
                primary_key=primary_key,
                write_disposition="merge",
                max_table_nesting=0,
                columns={
                    primary_key: {"data_type": "text"},
                    "iata_code": {"data_type": "text"},
                    "icao_code": {"data_type": "text"},
                    "extracted_at_utc": {
                        "data_type": "timestamp"
                    },
                },
            )
        )

        print(
            f"Validated {name}: {len(rows)} records"
        )

    return resources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without connecting",
    )

    args = parser.parse_args()
    resources = prepare_resources()

    if args.dry_run:
        print(
            "Validation passed. No web requests "
            "or Snowflake connection were made."
        )
        return

    secrets_path = BASE_DIR / ".dlt" / "secrets.toml"

    with secrets_path.open("rb") as file:
        credentials = tomllib.load(file)[
            "destination"
        ]["snowflake"]["credentials"]

    pipeline = dlt.pipeline(
        pipeline_name="wikipedia_reference",
        pipelines_dir=str(
            BASE_DIR / ".dlt" / "pipelines"
        ),
        destination=dlt.destinations.snowflake(
            credentials=credentials,
            staging_dataset_name_layout="%s_staging",
        ),
        dataset_name="raw",
    )

    print(pipeline.run(resources))


if __name__ == "__main__":
    main()