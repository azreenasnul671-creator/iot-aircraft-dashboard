import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), "flight_data.csv")
df = pd.read_csv(DATA_FILE)

# Configuration: set your Excel filename and optional sheet
EXCEL_FILE = "flight_data.csv"  # adjust if your file has a different name
EXCEL_SHEET = 0  # 0 for first sheet, or use sheet name like "Sheet1"

# Load dataset from Excel
def load_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"Failed to read CSV file: {e}")
        return pd.DataFrame()

# Optional: Harmonize column names to the expected schema
def harmonize_columns(df):
    rename_map = {
        # common variants
        'time': 'timestamp',
        'timestamp': 'timestamp',
        'date_time': 'timestamp',
        'lat': 'latitude',
        'latitude_deg': 'latitude',
        'latitude': 'latitude',
        'lon': 'longitude',
        'longitude_deg': 'longitude',
        'longitude': 'longitude',
        'callsign': 'callsign',
        'aircraft_callsign': 'callsign',
        'icao24': 'icao24',
        'icao_24': 'icao24',
        'alt': 'altitude',
        'altitude_m': 'altitude',
        'Altitude': 'altitude',
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df

# Load data
df = load_csv(DATA_FILE)
st.write(df.head())

# If loading failed or file is empty, show a helpful message and stop
if df is None or df.empty:
    st.title("Aircraft Monitoring Dashboard – Perak, Malaysia")
    st.info("Waiting for data. Please ensure flight_data.xlsx exists with the expected structure.")
    st.stop()

# Harmonize column names to expected schema
df = harmonize_columns(df)
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
df['altitude'] = pd.to_numeric(df['altitude'], errors='coerce')

# Ensure required columns exist; if not, warn and stop gracefully
required_cols = ['timestamp', 'latitude', 'longitude', 'callsign', 'icao24', 'altitude']
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.title("Aircraft Monitoring Dashboard – Perak, Malaysia")
    st.error(f"Missing required columns in Excel file: {', '.join(missing)}")
    st.info("Please adjust your Excel file or the harmonization mapping.")
    st.stop()

# Clean dataset (remove NODATA rows)
if 'icao24' in df.columns:
    df = df[df['icao24'].astype(str) != "NODATA"].copy()

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True, errors='coerce')

# Drop rows with missing critical fields to avoid downstream errors
df = df.dropna(subset=['timestamp', 'latitude', 'longitude', 'callsign', 'icao24'])

st.title("Aircraft Monitoring Dashboard – Perak, Malaysia")

# Sidebar Controls
st.sidebar.header("Filters")
shows_flights = sorted(df['callsign'].dropna().unique())
selectedflight = st.sidebar.selectbox(
    "Select a Callsign:",
    options=shows_flights
)

# SECTION 1: FLIGHT MAP
st.subheader("Live Aircraft Map – Perak")

mapdata = df.dropna(subset=['latitude','longitude'])

icon_data = {
    "url": "https://cdn-icons-png.flaticon.com/512/34/34627.png",
    "width": 128,
    "height": 128,
    "anchorY": 128
}

mapdata["icon"] = None
for i in mapdata.index:
    mapdata.at[i, "icon"] = icon_data

layer = pdk.Layer(
    "IconLayer",
    data=mapdata,
    get_icon="icon",
    get_size=4,
    size_scale=15,
    get_position="[longitude, latitude]",
    pickable=True
)

view_state = pdk.ViewState(
    latitude=4.0,
    longitude=101.0,
    zoom=7,
    pitch=45
)

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"text": "Flight: {callsign}\nAltitude: {altitude}"}
))
# SECTION 2: ALTITUDE GRAPH
st.subheader("Altitude Profile (Selected Flight)")

flightdf = df[df['callsign'] == selectedflight]

if len(flightdf) > 0:
    figalt = px.line(
        flightdf,
        x='timestamp',
        y='altitude',
        title=f"Altitude Over Time – {selectedflight}",
        markers=True
    )
    st.plotly_chart(figalt)
else:
    st.info("No altitude data available for this flight.")

# SECTION 3: NUMBER OF FLIGHTS OVER TIME
st.subheader("Flights Count Over Time")

# Create an hour-level timestamp
df['hour'] = df['timestamp'].dt.floor('H')
countdf = df.groupby('hour')['icao24'].nunique().reset_index()
countdf.rename(columns={'icao24': 'flightcount'}, inplace=True)

figcount = px.bar(
    countdf,
    x='hour',
    y='flightcount',
    title="Number of Flights Detected Per Hour"
)
st.plotly_chart(figcount)

st.write("Dashboard generated as part of IoT Aircraft Monitoring Project.")
