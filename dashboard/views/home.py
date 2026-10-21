import streamlit as st

from flight_data import finished_flights

flights = st.session_state["flights"]
finished = finished_flights(flights)

st.title("Flight Punctuality at Swedish Airports")
st.write(
    "This dashboard shows how many arrivals and departures are delayed at "
    "Swedish airports, and lets you compare airports, airlines and dates."
)
st.info(
    "A flight counts as delayed when it lands or departs more than "
    "15 minutes after its scheduled time. Flights that have not landed or "
    "departed yet are not counted as delayed or on time."
)

delayed = int(finished["is_delayed"].sum())
share = delayed / len(finished) if len(finished) else 0
avg_delay = finished["delay_minutes"].mean() if len(finished) else 0

cols = st.columns(5)
cols[0].metric("Flights", len(flights))
cols[1].metric("Delayed > 15 min", delayed)
cols[2].metric("Share delayed", f"{share:.1%}")
cols[3].metric("Average delay", f"{avg_delay:.1f} min")
cols[4].metric("Cancelled", int(flights["is_cancelled"].sum()))

st.subheader("How to use it")
st.markdown(
    "- Use the filters in the sidebar to pick dates, direction, airports or airlines.\n"
    "- Data shows the numbers as tables.\n"
    "- Charts shows the same numbers as graphs."
)

st.caption(
    "Sources: Swedavia FlightInfo API (arrivals and departures, last three days) "
    "and Wikipedia (airline and airport names)."
)
