"""Extract and cache the Wikipedia airline reference table."""

import hashlib
import json
import re
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

SOURCE_URL = "https://en.wikipedia.org/wiki/List_of_airline_codes"

SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "wikipedia_airlines.json"
)

USER_AGENT = (
    "FlightPunctualityAnalytics/0.1 "
    "(student project; "
    "https://github.com/mossadhagos/Flight_punctuality_analytics)"
)

COLUMN_NAMES = {
    "IATA": "iata_code",
    "ICAO": "icao_code",
    "Airline": "airline_name",
    "Telephony Designator": "callsign",
    "Country/Region": "country_region",
    "Comments": "comments",
}


def clean_text(value: str) -> str:
    """Remove citation markers and unnecessary whitespace."""
    value = re.sub(r"\[[^\]]*\]", "", str(value))
    return " ".join(value.split())


def parse_airlines(html_text: str) -> list[dict]:
    """Find the airline table and create reference records."""
    tables = pd.read_html(
        StringIO(html_text),
        keep_default_na=False,
    )

    matches = [
        table
        for table in tables
        if set(COLUMN_NAMES).issubset(table.columns)
    ]

    if len(matches) != 1:
        raise ValueError(
            "Expected one airline table. "
            "Wikipedia may have changed."
        )

    table = matches[0][list(COLUMN_NAMES)].rename(
        columns=COLUMN_NAMES
    )
    table = table.map(clean_text)

    unique_rows = {}

    for row in table.to_dict(orient="records"):
        encoded = json.dumps(
            row,
            sort_keys=True,
            ensure_ascii=False,
        )

        record_id = hashlib.sha256(
            encoded.encode("utf-8")
        ).hexdigest()

        unique_rows[record_id] = {
            "reference_id": record_id,
            **row,
            "source_url": SOURCE_URL,
        }

    print("Source rows:", len(table))
    print(
        "Identical duplicate rows removed:",
        len(table) - len(unique_rows),
    )

    return list(unique_rows.values())


def main() -> None:
    if SNAPSHOT_PATH.exists():
        snapshot = json.loads(
            SNAPSHOT_PATH.read_text(encoding="utf-8")
        )
        print(
            "Using saved Wikipedia snapshot. "
            "No request made."
        )

    else:
        response = requests.get(
            SOURCE_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=60,
        )
        response.raise_for_status()

        records = parse_airlines(response.text)

        if not records:
            raise ValueError(
                "No airline rows found. Nothing saved."
            )

        snapshot = {
            "source_url": SOURCE_URL,
            "extracted_at_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "airlines": records,
        }

        SNAPSHOT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = SNAPSHOT_PATH.with_suffix(".tmp")

        temporary_path.write_text(
            json.dumps(
                snapshot,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        temporary_path.replace(SNAPSHOT_PATH)

        print("Wikipedia airline snapshot saved.")

    print(
        "Airline reference records:",
        len(snapshot["airlines"]),
    )
    print("Extracted at:", snapshot["extracted_at_utc"])
    print("Snapshot:", SNAPSHOT_PATH)


if __name__ == "__main__":
    main()