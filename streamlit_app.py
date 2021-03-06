import pandas as pd
import streamlit as st
import altair as alt

DAILY_COUNTS_URL = "https://covidtracking.com/api/states/daily"
METRICS = [
    "positive",
    "negative",
    "death",
    "hospitalized",
    "positiveIncrease",
    "negativeIncrease",
    "deathIncrease",
    "hospitalizedIncrease",
    ]
DEFAULT_STATES = ["MA", "PA", "SC"]
DEFAULT_METRIC_INDEX = 2 # death
DEFAULT_START_DATE = pd.to_datetime("2020-03-01")
DEFAULT_END_DATE = pd.to_datetime("today")
STATE_POP_URL = ("https://raw.githubusercontent.com/JoshData/historical-state-population-csv/"
                 "primary/historical_state_population_by_year.csv")
PC_SUFFIX = "PerCapita"

# Cache downloading of the data so it doesn't re-download
# on change of user inputs.
@st.cache
def download_counts():
    # We need state populations for per-capita calculations
    state_pops = (pd.read_csv(STATE_POP_URL, names=["state", "year", "population"])
                  .query("year == year.max()")
                  .drop("year", axis=1))

    # Get the Covid data and convert the YYYYmmdd dates
    counts = (pd.read_json(DAILY_COUNTS_URL, dtype={"date": str})
              .assign(date = lambda x: pd.to_datetime(x["date"])))

    # Merge covid data with each state's population
    counts_pops = pd.merge(counts, state_pops, on="state", how="inner")

    # Add a per-capita version of each displayable metric
    for metric in METRICS:
        counts_pops[metric + PC_SUFFIX] = counts_pops[metric]/counts_pops["population"]
        
    return counts_pops

counts = download_counts()
states = list(counts["state"].unique())

st.title("US State Covid-19 Metrics")

selected_states = st.sidebar.multiselect("States", states, default=DEFAULT_STATES)
metric = st.sidebar.selectbox("Metric", METRICS, index=DEFAULT_METRIC_INDEX)
# For some reason, st.date_input doesn't produce an output type
# comparable with the DATE, so convert with PD.TO_DATETIME
start_date = pd.to_datetime(st.sidebar.date_input("Start date", value=DEFAULT_START_DATE))
end_date = pd.to_datetime(st.sidebar.date_input("End date", value=DEFAULT_END_DATE))
per_capita = st.sidebar.checkbox("Per capita")

# Include a pointer to thd data source
st.sidebar.markdown('Daily data from [covidtracking.com]("https://covidtracking.com")')

# Filter the data to the selected states and dates
selected_counts = counts[counts["state"].isin(selected_states) &
                         (counts["date"] >= start_date) &
                         (counts["date"] <= end_date)]

# Use appropriate metric for per-capita or not
chart_metric = (metric + PC_SUFFIX) if per_capita else metric

# Create Altair chart and display
chart = (alt.Chart(selected_counts)
         .mark_line()
         .encode(x="date", y=chart_metric, color="state"))
chart.height = 500
st.altair_chart(chart, use_container_width=True)




