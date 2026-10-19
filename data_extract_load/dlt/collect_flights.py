"""Collect today and the previous two UTC dates for all course airports."""

import json
import os
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

from data_extract_load.dlt.api_client import get_flights, recent_service_dates

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"

AIRPORTS = ("ARN", "BMA", "GOT", "MMX", "LLA", "UME", "OSD", "VBY", "RNB", "KRN")
DIRECTIONS = ("arrivals", "departures")


def snapshot_path_for(dates: tuple[date, ...]) -> Path:
    """Build a filename from the dates calculated for this run."""
    return DATA_DIR / f"flights_{dates[0].isoformat()}_{dates[-1].isoformat()}.json"


def read_snapshot(snapshot_path: Path, dates: tuple[date, ...]) -> dict:
    """Read a snapshot and check the expected dates and request coverage."""
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    if snapshot["dates"] != [day.isoformat() for day in dates]:
        raise ValueError("Snapshot dates do not match this collection window.")

    expected = {
        (airport, day.isoformat(), direction)
        for airport in AIRPORTS
        for day in dates
        for direction in DIRECTIONS
    }
    actual = {
        (item["airport_iata"], item["scheduled_date"], item["flight_type"])
        for item in snapshot["requests"]
    }

    if actual != expected or len(snapshot["requests"]) != len(expected):
        raise ValueError("Snapshot does not cover all 60 request combinations.")

    if sum(item["flight_count"] for item in snapshot["requests"]) != len(snapshot["flights"]):
        raise ValueError("Snapshot flight counts do not match.")

    return snapshot


def print_summary(snapshot: dict, snapshot_path: Path) -> None:
    """Show what was collected without displaying flight records or secrets."""
    print("\nDates:", ", ".join(snapshot["dates"]))
    print("Completed request combinations:", len(snapshot["requests"]))

    for direction in DIRECTIONS:
        count = sum(
            item["flight_count"]
            for item in snapshot["requests"]
            if item["flight_type"] == direction
        )
        print(f"{direction.capitalize()}: {count} records")

    print("Total flight records:", len(snapshot["flights"]))
    print("Snapshot:", snapshot_path)


def collect_flights() -> None:
    """Calculate the current window; reuse only a snapshot for those dates."""
    dates = recent_service_dates()
    snapshot_path = snapshot_path_for(dates)
    print("Collection window (UTC):", ", ".join(day.isoformat() for day in dates))

    if snapshot_path.exists():
        print("Using saved snapshot. No API requests will be made.")
        print_summary(read_snapshot(snapshot_path, dates), snapshot_path)
        return

    load_dotenv(PROJECT_DIR / ".env")
    api_key = os.getenv("SWEDAVIA_API_KEY", "").strip()

    if not api_key:
        raise SystemExit("SWEDAVIA_API_KEY is missing from your local .env.")

    all_flights = []
    completed_requests = []
    total_requests = len(AIRPORTS) * len(dates) * len(DIRECTIONS)

    with requests.Session() as session:
        for airport in AIRPORTS:
            for day in dates:
                for direction in DIRECTIONS:
                    flights = get_flights(
                        api_key=api_key,
                        airport_iata=airport,
                        direction=direction,
                        service_date=day,
                        session=session,
                    )
                    extracted_at = datetime.now(timezone.utc).isoformat()

                    for flight in flights:
                        flight_id = flight.get("flightId") or flight.get("FlightId")

                        if flight_id is None or not str(flight_id).strip():
                            raise ValueError(
                                f"Missing flight ID: {airport} {direction} {day}"
                            )

                        row = dict(flight)
                        row.pop("flightId", None)
                        row.pop("FlightId", None)
                        row.update(
                            flight_id=str(flight_id),
                            airport_iata=airport,
                            scheduled_date=day.isoformat(),
                            flight_type=direction,
                            extracted_at_utc=extracted_at,
                        )
                        all_flights.append(row)

                    completed_requests.append(
                        {
                            "airport_iata": airport,
                            "scheduled_date": day.isoformat(),
                            "flight_type": direction,
                            "flight_count": len(flights),
                            "extracted_at_utc": extracted_at,
                        }
                    )

                    print(
                        f"[{len(completed_requests)}/{total_requests}] "
                        f"{airport} {direction} {day}: {len(flights)} records",
                        flush=True,
                    )
                    time.sleep(1)

    if not all_flights:
        raise SystemExit("Every request was empty. No snapshot was saved; investigate first.")

    snapshot = {
        "dates": [day.isoformat() for day in dates],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "requests": completed_requests,
        "flights": all_flights,
    }

    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = snapshot_path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_path.replace(snapshot_path)

    print("Collection complete. Snapshot saved.")
    print_summary(read_snapshot(snapshot_path, dates), snapshot_path)


if __name__ == "__main__":
    collect_flights()