from datetime import date

import pytest

from data_extract_load.dlt.api_client import get_flights, recent_service_dates


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        pass

    def json(self):
        if self.status_code == 204:
            raise ValueError("No JSON body for HTTP 204")
        return self.payload


class FakeSession:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def get(self, url, *, headers, timeout):
        self.url = url
        self.headers = headers
        self.timeout = timeout
        return FakeResponse(self.payload, self.status_code)


def test_get_flights_builds_request_and_returns_flights():
    session = FakeSession({"Flights": [{"FlightId": "SK123"}]})

    flights = get_flights(
        api_key="fake-test-key",
        airport_iata="ARN",
        direction="departures",
        service_date=date(2026, 10, 13),
        session=session,
    )

    assert flights == [{"FlightId": "SK123"}]
    assert session.url.endswith("/ARN/departures/2026-10-13")
    assert session.headers["Ocp-Apim-Subscription-Key"] == "fake-test-key"
    assert session.timeout == 30


def test_get_flights_returns_empty_list_when_api_has_no_flights():
    session = FakeSession({"Flights": None})

    flights = get_flights(
        api_key="fake-test-key",
        airport_iata="ARN",
        direction="arrivals",
        service_date=date(2026, 10, 13),
        session=session,
    )

    assert flights == []


def test_get_flights_rejects_response_without_flights_field():
    session = FakeSession({})

    with pytest.raises(ValueError, match="missing the 'Flights' field"):
        get_flights(
            api_key="fake-test-key",
            airport_iata="ARN",
            direction="arrivals",
            service_date=date(2026, 10, 13),
            session=session,
        )


def test_recent_service_dates_returns_three_consecutive_dates():
    dates = recent_service_dates(date(2026, 10, 13))

    assert dates == (
        date(2026, 10, 11),
        date(2026, 10, 12),
        date(2026, 10, 13),
    )


def test_get_flights_accepts_lowercase_flights_field():
    session = FakeSession({"flights": [{"flightId": "SK123"}]})

    flights = get_flights(
        api_key="fake-test-key",
        airport_iata="ARN",
        direction="arrivals",
        service_date=date(2026, 10, 13),
        session=session,
    )

    assert flights == [{"flightId": "SK123"}]


def test_get_flights_returns_empty_list_for_http_204():
    session = FakeSession(None, status_code=204)

    flights = get_flights(
        api_key="fake-test-key",
        airport_iata="ARN",
        direction="arrivals",
        service_date=date(2026, 10, 13),
        session=session,
    )

    assert flights == []