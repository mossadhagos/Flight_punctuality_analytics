import streamlit as st

from flight_data import delay_summary, finished_flights

flights = st.session_state["flights"]
finished = finished_flights(flights)

st.title("Charts")

st.subheader("Delayed flights per day")
per_day = finished.groupby(["flight_date", "direction"])["is_delayed"].sum()
st.bar_chart(per_day.unstack())

left, right = st.columns(2)

left.subheader("% delayed by airport")
left.bar_chart(delay_summary(flights, "airport_name")["pct_delayed"])

right.subheader("Arrivals vs departures per airport")
by_direction = delay_summary(flights, ["airport_name", "direction"])["pct_delayed"]
right.bar_chart(by_direction.unstack(), stack=False)

st.subheader("% delayed by airline")
min_flights = st.slider("Only airlines with at least this many flights", 1, 50, 10)
by_airline = delay_summary(flights, "airline_name")
st.bar_chart(by_airline[by_airline["flights"] >= min_flights]["pct_delayed"])
