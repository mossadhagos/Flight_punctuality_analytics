"""Collect Wikipedia reference information for the ten project airports."""

import json
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from lxml import html

from data_extract_load.collect_airlines import USER_AGENT, clean_text
from data_extract_load.collect_flights import AIRPORTS

INTERNATIONAL_URL = (
    "https://en.wikipedia.org/wiki/"
    "List_of_international_airports_by_country"
)
SWEDEN_URL = "https://en.wikipedia.org/wiki/List_of_airports_in_Sweden"

SNAPSHOT_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "wikipedia_airports.json"
)


def validate_airports(records: list[dict]) -> None:
    """Require one complete reference record per project airport."""
    codes = [row["iata_code"] for row in records]

    if len(codes) != len(AIRPORTS) or set(codes) != set(AIRPORTS):
        raise ValueError(
            "Airport reference must cover each project airport exactly once."
        )

    for row in records:
        required = (
            "airport_name",
            "city",
            "country",
            "icao_code",
            "source_urls",
        )

        if not all(row.get(field) for field in required):
            raise ValueError(
                f"Incomplete airport reference: {row['iata_code']}"
            )


def parse_airports(
    international_html: str,
    sweden_html: str,
) -> list[dict]:
    """Combine the Sweden section with the Swedish airport table."""
    root = html.fromstring(international_html)
    headings = root.xpath('//*[@id="Sweden"]')

    if len(headings) != 1:
        raise ValueError(
            "Cannot identify the Sweden section on Wikipedia."
        )

    tables = headings[0].xpath("following::table[1]")

    if not tables:
        raise ValueError(
            "No airport table after the Sweden heading."
        )

    international = pd.read_html(
        StringIO(
            html.tostring(tables[0], encoding="unicode")
        ),
        keep_default_na=False,
    )[0]

    international.columns = [
        clean_text(column)
        for column in international.columns
    ]

    if not {"IATA Code", "Location", "Airport"}.issubset(
        international.columns
    ):
        raise ValueError(
            "International-airport table columns have changed."
        )

    international = international.map(clean_text)

    candidates = []

    for table in pd.read_html(
        StringIO(sweden_html),
        keep_default_na=False,
    ):
        table.columns = [
            clean_text(column)
            for column in table.columns
        ]

        required = {
            "IATA",
            "ICAO",
            "City served",
            "Airport name",
            "Runway(s)",
        }

        if required.issubset(table.columns):
            candidates.append(table.map(clean_text))

    if len(candidates) != 1:
        raise ValueError(
            "Expected one Swedish-airport table. "
            "Check Wikipedia layout."
        )

    swedish = candidates[0]
    records = []
    supplemented = []

    for code in AIRPORTS:
        local = swedish.loc[swedish["IATA"] == code]
        primary = international.loc[
            international["IATA Code"] == code
        ]

        if len(local) != 1 or len(primary) > 1:
            raise ValueError(
                f"Missing or ambiguous airport reference: {code}"
            )

        local_row = local.iloc[0]
        name = local_row["Airport name"]
        city = local_row["City served"]
        sources = [SWEDEN_URL]

        if not primary.empty:
            name = primary.iloc[0]["Airport"]
            city = primary.iloc[0]["Location"]
            sources.insert(0, INTERNATIONAL_URL)
        else:
            supplemented.append(code)

        records.append(
            {
                "iata_code": code,
                "icao_code": local_row["ICAO"],
                "airport_name": name,
                "city": city,
                "country": "Sweden",
                "source_urls": sources,
            }
        )

    validate_airports(records)

    print(
        "Supplemented from Swedish list:",
        ", ".join(supplemented) or "None",
    )

    return records


def main() -> None:
    if SNAPSHOT_PATH.exists():
        snapshot = json.loads(
            SNAPSHOT_PATH.read_text(encoding="utf-8")
        )
        print(
            "Using saved Wikipedia snapshot. "
            "No requests made."
        )

    else:
        with requests.Session() as session:
            session.headers.update(
                {"User-Agent": USER_AGENT}
            )

            pages = []

            for url in (INTERNATIONAL_URL, SWEDEN_URL):
                response = session.get(url, timeout=60)
                response.raise_for_status()
                pages.append(response.text)

        records = parse_airports(*pages)

        snapshot = {
            "extracted_at_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "airports": records,
        }

        SNAPSHOT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = SNAPSHOT_PATH.with_suffix(".tmp")

        temporary.write_text(
            json.dumps(
                snapshot,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        temporary.replace(SNAPSHOT_PATH)
        print("Wikipedia airport snapshot saved.")

    validate_airports(snapshot["airports"])

    print(
        "Airport reference records:",
        len(snapshot["airports"]),
    )
    print(
        "Codes:",
        ", ".join(
            row["iata_code"]
            for row in snapshot["airports"]
        ),
    )
    print("Snapshot:", SNAPSHOT_PATH)


if __name__ == "__main__":
    main()