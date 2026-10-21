import streamlit as st

from flight_data import delay_summary

COLUMNS = [
    "flight_date", "direction", "flight_number", "airline_name", "airport_name",
    "other_airport_iata", "scheduled_at_utc", "actual_at_utc", "delay_minutes",
    "flight_status",
]

flights = st.session_state["flights"]

st.title("Data")

st.subheader("By airport")
st.dataframe(delay_summary(flights, "airport_name"))

st.subheader("By airline")
min_flights = st.slider("Only airlines with at least this many flights", 1, 50, 10)
by_airline = delay_summary(flights, "airline_name")
st.dataframe(by_airline[by_airline["flights"] >= min_flights])

st.subheader("Arrivals vs departures")
st.dataframe(delay_summary(flights, "direction"))

st.subheader("Most delayed flights")
st.dataframe(flights.nlargest(20, "delay_minutes")[COLUMNS], hide_index=True)

st.subheader("Find a flight")
query = st.text_input("Flight number, e.g. SK1045").strip().upper()
if query:
    found = flights[flights["flight_number"].str.contains(query, na=False)]
    st.dataframe(found[COLUMNS], hide_index=True)
