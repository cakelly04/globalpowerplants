"""
CS230 Final Project: Global Power Plants Explorer
Student: Cameron Kelly
Section: CS230-7
Dataset: power_plants_6_countries.csv
Source: World Resources Institute, Global Power Plant Database (CC BY 4.0).
Description: Interactive country, fuel-type, capacity, and location analysis
             for someone researching the energy sector.
AI coding partner: ChatGPT (OpenAI)
Streamlit Cloud URL: ADD YOUR APP URL AFTER PUBLISHING
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st


# #[DICT_DRIVEN] AUGMENT
# I added dictionaries to keep chart labels consistent and to choose a useful
# starting map zoom for each country. For example, "capacity_mw" always displays
# as "Generation Capacity (MW)", and Brazil starts more zoomed out than France.
LABELS = {
    "capacity_mw": "Generation Capacity (MW)",
    "name": "Power Plant",
    "primary_fuel": "Fuel Type",
}

MAP_ZOOM = {
    "Brazil": 3,
    "Canada": 3,
    "France": 5,
    "Germany": 5,
    "India": 4,
    "United Kingdom": 5,
}


# #[REUSE_FUNC] REVISE / REWRITE
# The earlier program repeated the country-filtering code in every question.
# I replaced those repeated sections with one function that can also filter
# by fuel type. For example, select_plants(df, "Brazil", "Solar") returns
# only Brazilian solar plants; leaving fuel out returns all Brazilian plants.
def select_plants(data, country, fuel=None):
    selected = data[data["country_long"] == country]
    if fuel is not None:
        selected = selected[selected["primary_fuel"] == fuel]
    return selected


# #[INPUT_CHECK] AUGMENT
# I added checks for a missing or unreadable CSV, missing columns, and bad
# numeric values. A missing file now shows a helpful message instead of an
# exception; unusable records are excluded before charts are created.
DATA_FILE = Path(__file__).parent / "power_plants_6_countries.csv"

try:
    df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    st.error("Power plant CSV not found. Put it in the same folder as app.py.")
    st.stop()
except Exception as error:
    st.error(f"Could not read the power plant CSV: {error}")
    st.stop()

required_columns = [
    "country_long", "name", "primary_fuel",
    "capacity_mw", "latitude", "longitude"
]

# #[LIST_COMP] IDENTIFY & EXPLAIN
# This list comprehension checks each required column against the CSV headers.
# For example, if "latitude" is missing, it appears in missing_columns and
# the app shows a warning instead of trying to build a map without latitude.
missing_columns = [column for column in required_columns if column not in df.columns]

if missing_columns:
    st.error(f"The dataset is missing these columns: {', '.join(missing_columns)}")
    st.stop()

# Convert capacity and coordinates to numbers and remove unusable rows.
for column in ["capacity_mw", "latitude", "longitude"]:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = df.dropna(subset=["country_long", "name", "primary_fuel", "capacity_mw"])
df = df[df["capacity_mw"] > 0]

if df.empty:
    st.error("No usable power plants were found in the dataset.")
    st.stop()

countries = sorted(df["country_long"].unique())

# Navigation lets the user see everything or explore one question at a time.
st.sidebar.title("Navigation")
section = st.sidebar.radio(
    "Choose a section:",
    ["All sections", "Largest plants", "Plants by fuel", "Capacity mix", "Power plant map"]
)

st.title("Global Power Plants Explorer")
st.write(
    "Explore power plants in Brazil, Canada, France, Germany, India, "
    "and the United Kingdom. This tool is designed for an energy-sector "
    "investor comparing the size, fuel mix, and locations of power plants."
)
st.info(
    "Capacity is measured in megawatts (MW). This is a plant's rated "
    "generating capacity, not the electricity it actually generates."
)

with st.expander("View dataset preview and source"):
    st.write(f"**Records in the cleaned dataset:** {len(df):,}")
    st.dataframe(df.head(), hide_index=True)
    st.caption(
        "Source: World Resources Institute, Global Power Plant Database "
        "(CC BY 4.0). This historical dataset is no longer updated."
    )


# Question 1: Largest power plants in a country.
if section == "All sections" or section == "Largest plants":
    st.header("Question 1: Largest Power Plants by Country")
    selected_country = st.selectbox("Select a country:", countries, key="q1_country")

    filtered_df = select_plants(df, selected_country)
    top_10 = filtered_df.sort_values("capacity_mw", ascending=False).head(10)

    if top_10.empty:
        st.warning("No power plants were found for this country.")
    else:
        st.write(f"The 10 largest power plants in **{selected_country}** by capacity:")
        # Sort in the opposite order so the largest bar appears at the top.
        top_10_chart = top_10.sort_values("capacity_mw")
        fig1 = px.bar(
            top_10_chart,
            x="capacity_mw",
            y="name",
            orientation="h",
            color="capacity_mw",
            color_continuous_scale="Blues",
            title=f"10 Largest Power Plants in {selected_country}",
            labels=LABELS,
            hover_data={"capacity_mw": ":,.1f"}
        )
        fig1.update_layout(
            height=550,
            showlegend=False,
            coloraxis_showscale=False,
            yaxis_title=None,
            xaxis_title=LABELS["capacity_mw"]
        )
        st.plotly_chart(fig1, use_container_width=True)
        st.caption("These rankings compare rated capacity, not annual generation.")


# Question 2: Count and list plants matching a country and fuel type.
if section == "All sections" or section == "Plants by fuel":
    st.header("Question 2: Power Plants by Fuel Type")
    q2_country = st.selectbox("Select a country for Question 2:", countries, key="q2_country")
    country_df = select_plants(df, q2_country)
    fuel_types = sorted(country_df["primary_fuel"].dropna().unique())

    if not fuel_types:
        st.warning("No fuel types were found for this country.")
    else:
        selected_fuel = st.selectbox("Select a fuel type:", fuel_types)
        matching_plants = select_plants(df, q2_country, selected_fuel)

        st.metric(
            label=f"{selected_fuel} power plants in {q2_country}",
            value=f"{len(matching_plants):,}"
        )
        st.subheader("Matching Power Plants")
        if matching_plants.empty:
            st.warning("No plants match these selections.")
        else:
            matching_plants = matching_plants.sort_values("capacity_mw", ascending=False)
            st.dataframe(
                matching_plants[["name", "country_long", "primary_fuel", "capacity_mw"]],
                hide_index=True
            )
        st.caption("Each row represents one plant in the supplied database.")


# Question 3: Compare total rated capacity by primary fuel type.
if section == "All sections" or section == "Capacity mix":
    st.header("Question 3: Generation Capacity by Fuel Type")
    q3_country = st.selectbox("Select a country for Question 3:", countries, key="q3_country")
    q3_df = select_plants(df, q3_country)

    fuel_capacity = (
        q3_df.groupby("primary_fuel")["capacity_mw"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    if fuel_capacity.empty:
        st.warning("No capacity data is available for this country.")
    else:
        st.write(f"Share of total rated capacity by fuel type in **{q3_country}**:")
        fig3 = px.pie(
            fuel_capacity,
            names="primary_fuel",
            values="capacity_mw",
            hole=0.45,
            title=f"Generation Capacity by Fuel Type in {q3_country}",
            color_discrete_sequence=px.colors.qualitative.Set2,
            labels=LABELS
        )
        fig3.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate=(
                "<b>%{label}</b><br>Share: %{percent}<br>"
                "Capacity: %{value:,.1f} MW<extra></extra>"
            )
        )
        fig3.update_layout(height=550, legend_title_text="Fuel Type")
        st.plotly_chart(fig3, use_container_width=True)

        biggest_fuel = fuel_capacity.iloc[0]
        total_capacity = fuel_capacity["capacity_mw"].sum()
        percent = biggest_fuel["capacity_mw"] / total_capacity * 100
        st.write(
            f"**Key finding:** {biggest_fuel['primary_fuel']} has the greatest "
            f"rated capacity in {q3_country}, at approximately {percent:.1f}% of the total."
        )
        st.subheader("Capacity Breakdown")
        st.dataframe(
            fuel_capacity.rename(columns={
                "primary_fuel": LABELS["primary_fuel"],
                "capacity_mw": "Total Capacity (MW)"
            }),
            hide_index=True
        )
        st.caption("These percentages measure capacity, not electricity production or consumption.")


# Interactive map: Customized PyDeck circles for the 200 largest plants.
if section == "All sections" or section == "Power plant map":
    st.header("Interactive Power Plant Map")
    map_country = st.selectbox("Select a country for the map:", countries, key="map_country")
    map_df = select_plants(df, map_country).copy()

    # A map needs valid coordinates; exclude rows without usable locations.
    map_df = map_df.dropna(subset=["latitude", "longitude"])
    map_df = map_df[
        map_df["latitude"].between(-90, 90) &
        map_df["longitude"].between(-180, 180)
    ]
    map_df = map_df.nlargest(200, "capacity_mw").copy()

    if map_df.empty:
        st.warning("No power plants with valid map coordinates were found.")
    else:
        # Larger capacity -> larger circle; square root keeps sizes readable.
        map_df["radius"] = map_df["capacity_mw"].clip(lower=1) ** 0.5 * 150

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position="[longitude, latitude]",
            get_radius="radius",
            get_fill_color=[30, 120, 220, 160],
            pickable=True,
            auto_highlight=True
        )
        view_state = pdk.ViewState(
            latitude=float(map_df["latitude"].mean()),
            longitude=float(map_df["longitude"].mean()),
            zoom=MAP_ZOOM.get(map_country, 4),
            pitch=0
        )
        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                "html": (
                    "<b>{name}</b><br/>Fuel: {primary_fuel}<br/>"
                    "Capacity: {capacity_mw} MW"
                ),
                "style": {"backgroundColor": "steelblue", "color": "white"}
            }
        )
        st.pydeck_chart(deck)
        st.caption(
            "The map shows up to 200 of the largest plants in the selected "
            "country. Hover over a circle for the plant's details; "
            "larger circles mean greater rated capacity."
        )

# #[DEPLOY] IDENTIFY & EXPLAIN — COMPLETE AFTER CLOUD PUBLICATION.
# The CSV is located relative to app.py and the libraries are in requirements.txt.
# These allow Streamlit Community Cloud to install dependencies and load the file.
# After publishing, paste the real URL into the docstring and the course sign-up
# sheet, and document any deployment issue you had to solve.
