"""Client for retrieving flight data from Swedavia's FlightInfo API."""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

import requests

FlightDirection = Literal["arrivals", "departures"]
BASE_URL = "https://api.swedavia.se/flightinfo/v2"


def get_flights(
    api_key: str,
    airport_iata: str,
    direction: FlightDirection,
    service_date: date,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Fetch flights for one airport, direction, and date."""

    url = (
        f"{BASE_URL}/{airport_iata}/{direction}/"
        f"{service_date.isoformat()}"
    )

    http = session if session is not None else requests

    response = http.get(
        url,
        headers={
            "Accept": "application/json",
            "Ocp-Apim-Subscription-Key": api_key,
        },
        timeout=30,
    )

    response.raise_for_status()

    if response.status_code == 204:
        return []

    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("Expected the FlightInfo API to return a JSON object.")

    flight_key = "Flights" if "Flights" in payload else "flights"

    if flight_key not in payload:
        raise ValueError("FlightInfo response is missing the 'Flights' field.")

    flights = payload[flight_key]

    if flights is None:
        return []

    if not isinstance(flights, list):
        raise ValueError("Expected the 'Flights' field to be a list.")

    if not all(isinstance(flight, dict) for flight in flights):
        raise ValueError("Expected each flight to be a JSON object.")

    return flights


def recent_service_dates(today_utc: date | None = None) -> tuple[date, ...]:
    """Return the two previous dates and today, using UTC."""

    end_date = today_utc or datetime.now(timezone.utc).date()

    return tuple(
        end_date - timedelta(days=days_ago)
        for days_ago in (2, 1, 0)
    )