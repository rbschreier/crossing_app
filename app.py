# Channel Cross - Santa Barbara Channel Crossing Planner
# Powered by Stormglass API - 10-Day Forecast
# Author: ME!

import json
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta, UTC

# --------------------------
# App Configuration
# --------------------------

st.set_page_config(page_title="Channel Cross", page_icon="🛥️",layout="wide")
st.title("Channel Cross - 10-Day Marine Forecast (Powered by Stormglass)")

st.markdown(
    """
    <div style='font-family: Arial'>
    This app provides a <b>10-day forward forecast</b> for the Santa Barbara Channel 
    using the <a href="https://stormglass.io">Stormglass.io</a> Marine API.<br><br>
    Forecast includes <b>wind, cloud cover, swell height, swell period, and swell direction</b> 
    to help find days for Dee trips.
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------
# Sidebar - User Crossing Parameters
# --------------------------

st.sidebar.header("Set Your Preferred Crossing Conditions")

wind_speed_max = st.sidebar.slider("Max Wind Speed (knots)", 5, 25, 12)
cloud_cover_max = st.sidebar.slider("Max Cloud Cover (%)", 0, 100, 80)
swell_height_max = st.sidebar.slider("Max Swell Height (ft)", 0, 15, 3)
swell_period_min = st.sidebar.slider("Min Swell Period (sec)", 5, 20, 9)

# --------------------------
# Fetch Forecast Data from Stormglass API
# --------------------------

api_key = st.secrets["API_KEY"]
lat = 34.4
lon = -119.7

start_date = datetime.now()
end_date = start_date + timedelta(days=10)

start_iso = start_date.isoformat() + 'Z'
end_iso = end_date.isoformat() + 'Z'

# I assume these are the API parameters for the Stormglass API
params = [
    'swellHeight',
    'swellPeriod',
    'swellDirection',
    'windSpeed',
    'windDirection',
    'cloudCover'
]

url = (
    f"https://api.stormglass.io/v2/weather/point"
    f"?lat={lat}&lng={lon}"
    f"&params={','.join(params)}"
    f"&start={start_iso}&end={end_iso}"
    f"&source=noaa"
)

#LIVE API DATA
response = requests.get(
    url,
    headers={
        'Authorization': api_key
    }
)

if response.status_code != 200:
    st.error(f"Error fetching data from Stormglass API: {response.status_code} {response.text}")
    st.stop()
data = response.json()


# DUMMY DATA LOAD FROM FILE
# with open("dummy_data.json", "r") as f:
#    data = json.load(f)



# DUMMY DATA: Save the raw API response to a file for dummy data
#with open("dummy_data.json", "w") as f:
#    json.dump(response.json(), f, indent=2)

# --------------------------
# Process Data - Aggregate Daily Values
# --------------------------

df = pd.json_normalize(data['hours'])
df['time'] = pd.to_datetime(df['time'])
df['date'] = df['time'].dt.date

df_daily = df.groupby('date').agg({
    'windSpeed.noaa': 'max',
    'cloudCover.noaa': 'mean',
    'swellHeight.noaa': 'max',
    'swellPeriod.noaa': 'mean',
    'swellDirection.noaa': 'mean'
}).reset_index()

df_daily.rename(columns={
    'windSpeed.noaa': 'wind_speed',
    'cloudCover.noaa': 'cloud_cover',
    'swellHeight.noaa': 'swell_height',
    'swellPeriod.noaa': 'swell_period',
    'swellDirection.noaa': 'swell_direction'
}, inplace=True)

df_daily['swell_height'] = df_daily['swell_height'] * 3.28084

# --------------------------
# Determine Crossing Suitability
# --------------------------

df_daily['suitable'] = (
    (df_daily['wind_speed'] <= wind_speed_max) &
    (df_daily['cloud_cover'] <= cloud_cover_max) &
    (df_daily['swell_height'] <= swell_height_max) &
    (df_daily['swell_period'] >= swell_period_min)
)

# --------------------------
# Format for Display
# --------------------------

nice_column_names = {
    'date': 'Date',
    'wind_speed': 'Wind Speed',
    'cloud_cover': 'Cloud Cover',
    'swell_height': 'Swell Height',
    'swell_period': 'Swell Period',
    'swell_direction': 'Swell Direction',
    'suitable': 'Suitability'
}

df_display_final = df_daily.copy()
df_display_final['wind_speed'] = df_display_final['wind_speed'].map(lambda x: f"{x:.1f} kn")
df_display_final['cloud_cover'] = df_display_final['cloud_cover'].map(lambda x: f"{int(round(x))} %")
df_display_final['swell_height'] = df_display_final['swell_height'].map(lambda x: f"{x:.1f} ft")
df_display_final['swell_period'] = df_display_final['swell_period'].map(lambda x: f"{x:.1f} s")
df_display_final['swell_direction'] = df_display_final['swell_direction'].map(lambda x: f"{int(round(x))} °")
df_display_final['suitable'] = df_daily['suitable'].map(lambda x: "✅ Good" if x else "❌ Poor")

df_display_final.rename(columns=nice_column_names, inplace=True)

# --------------------------
# Row Styling Function
# --------------------------

def row_style(row):
    if row['Suitability'] == "✅ Good":
        return ['background-color: #d0f0c0'] * len(row)
    else:
        return [''] * len(row)

# --------------------------
# Display Table (No Scroll)
# --------------------------

st.subheader("10-Day Marine Forecast (Formatted View)")

styled_df = df_display_final.style.apply(row_style, axis=1)
st.dataframe(styled_df)
