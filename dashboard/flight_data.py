import pandas as pd
import streamlit as st


@st.cache_data(ttl=600)
def load_flights() -> pd.DataFrame:
    conn = st.connection("snowflake")
    df = conn.query("select * from mart_flight_punctuality", ttl=600)
    df.columns = df.columns.str.lower()
    df["flight_date"] = pd.to_datetime(df["flight_date"]).dt.date
    df["delay_minutes"] = pd.to_numeric(df["delay_minutes"])
    df["is_delayed"] = df["is_delayed"].astype("boolean")
    df["is_cancelled"] = df["is_cancelled"].astype("boolean")
    return df

def pick(label: str, df: pd.DataFrame, column: str) -> pd.DataFrame:
    options = sorted(df[column].dropna().unique())
    chosen = st.sidebar.multiselect(label, options)
    return df[df[column].isin(chosen)] if chosen else df


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")
    dates = st.sidebar.date_input(
        "Dates", value=(df["flight_date"].min(), df["flight_date"].max())
    )
    if len(dates) == 2:
        df = df[df["flight_date"].between(dates[0], dates[1])]
    df = pick("Direction", df, "direction")
    df = pick("Airport", df, "airport_name")
    df = pick("Airline", df, "airline_name")
    return df


def finished_flights(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["is_delayed"].notna()]

def delay_summary(df: pd.DataFrame, by) -> pd.DataFrame:
    summary = finished_flights(df).groupby(by).agg(
        flights=("is_delayed", "size"),
        delayed=("is_delayed", "sum"),
        avg_delay_min=("delay_minutes", "mean"),
    )
    summary["pct_delayed"] = summary["delayed"].div(summary["flights"]).mul(100).round(1)
    summary["avg_delay_min"] = summary["avg_delay_min"].round(1)
    return summary.sort_values("pct_delayed", ascending=False)
