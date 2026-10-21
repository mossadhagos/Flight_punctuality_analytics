import streamlit as st

from flight_data import apply_filters, load_flights

st.set_page_config(page_title="Flight Punctuality", layout="wide")

pages = st.navigation([
    st.Page("views/home.py", title="Home", default=True),
    st.Page("views/tables.py", title="Data"),
    st.Page("views/charts.py", title="Charts"),
])

flights = apply_filters(load_flights())
if flights.empty:
    st.warning("No flights match the filters.")
    st.stop()

st.session_state["flights"] = flights
pages.run()
