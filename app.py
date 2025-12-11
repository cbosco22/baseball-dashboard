import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.title("College Baseball Player Dashboard")

# Reset button in sidebar
st.sidebar.header("Filters")
if st.sidebar.button("Reset All Filters"):
    st.session_state.clear()
    st.rerun()

@st.cache_data
def load_data():
    pitchers = pd.read_csv('pitchers.csv')
    hitters = pd.read_csv('hitters.csv')
    pitchers['role'] = 'Pitcher'
    hitters['role'] = 'Hitter'
    df = pd.concat([pitchers, hitters], ignore_index=True, sort=False)

    # State
    df['state'] = df['hsplace'].str.split(',').str[-1].str.strip().str.upper()
    us_states = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
    df = df[df['state'].isin(us_states)]

    # Draft cleanup
    df['draft_year'] = pd.to_numeric(df['draft_year'], errors='coerce')
    df['draft_Round'] = pd.to_numeric(df['draft_Round'], errors='coerce').fillna(0)
    df['is_drafted'] = df['draft_year'].notna()

    # Region mapping
    region_map = {
        'East': ['KY','OH','PA','TN','WV'],
        'Mid Atlantic': ['DE','MD','NJ','NY','VA'],
        'Midwest I': ['IL','IN','IA','KS','MI','MN','MO','NE','ND','SD','WI'],
        'Midwest II': ['AR','OK','TX'],
        'New England': ['CT','ME','MA','NH','RI','VT'],
        'South': ['AL','FL','GA','LA','MS','NC','SC'],
        'West': ['AK','AZ','CA','CO','HI','ID','MT','NV','NM','OR','UT','WA','WY'],
    }
    def get_region(s):
        for r, states in region_map.items():
            if s in states:
                return r
        return 'Other'
    df['region'] = df['state'].apply(get_region)

    # T90s and T90/PA
    df['Singles'] = df['H'] - df['Dbl'] - df['Tpl'] - df['HR']
    df['Singles'] = df['Singles'].fillna(0)
    df['TotalBases'] = df['Singles'] + 2*df['Dbl'].fillna(0) + 3*df['Tpl'].fillna(0) + 4*df['HR'].fillna(0)
    df['T90s'] = df['TotalBases'] + df['SB'].fillna(0) + df['BB'].fillna(0) + df['HBP'].fillna(0)
    df['PA'] = df['AB'].fillna(0) + df['BB'].fillna(0) + df['HBP'].fillna(0) + df['SF'].fillna(0) + df['SH'].fillna(0)
    df['T90_per_PA'] = df['T90s'] / df['PA'].replace(0, np.nan)
    df['T90_per_PA'] = df['T90_per_PA'].fillna(0)

    # Clean height and weight
    df['ht'] = pd.to_numeric(df['ht'], errors='coerce')
    df['WT'] = pd.to_numeric(df['WT'], errors='coerce')

    # Clean Bats and Throws
    df['Bats'] = df['Bats'].str.upper().replace('B', 'S')
    df['Throws'] = df['Throws'].str.upper()

    # Clean and standardize position (all caps)
    df['posit'] = df['posit'].str.upper().str.strip()

    return df

data = load_data()

# Get unique positions (all caps)
unique_positions = sorted(data['posit'].dropna().unique())

# Position multiselect with "contains" shortcut
position_search = st.sidebar.text_input("Quick Position Search (e.g., SS for all shortstops)", key="position_search")
if position_search:
    matching_positions = [p for p in unique_positions if position_search.upper() in p]
    position_filter = st.sidebar.multiselect("Position (selected by search)", options=unique_positions, default=matching_positions, key="posit")
else:
    position_filter = st.sidebar.multiselect("Position", options=unique_positions, key="posit")

# Bats and Throws
bats_filter = st.sidebar.multiselect("Bats", options=['L', 'R', 'S'], key="bats")
throws_filter = st.sidebar.multiselect("Throws", options=['L', 'R'], key="throws")

# Height and Weight sliders - safe defaults
ht_min = int(data['ht'].min()) if data['ht'].notna().any() else 60
ht_max = int(data['ht'].max()) if data['ht'].notna().any() else 80
wt_min = int(data['WT'].min()) if data['WT'].notna().any() else 150
wt_max = int(data['WT'].max()) if data['WT'].notna().any() else 250

ht_range = st.sidebar.slider("Height (inches)", min_value=ht_min, max_value=ht_max, value=(ht_min, ht_max), key="ht")
wt_range = st.sidebar.slider("Weight (lbs)", min_value=wt_min, max_value=wt_max, value=(wt_min, wt_max), key="wt")

# Other filters...
# (All other filters from previous version: role, league, team, year, state, region, min_games, drafted, draft_round, custom stat filters, name_search)

# Base filtering (same as before, with position_filter using the new variable)
filtered = data[
    data['role'].isin(role_filter) &
    data['year'].between(*year_filter) &
    (data['G'] >= min_games)
]

if league_filter:
    filtered = filtered[filtered['LeagueAbbr'].isin(league_filter)]
if team_filter:
    filtered = filtered[filtered['teamName'].isin(team_filter)]
if state_filter:
    filtered = filtered[filtered['state'].isin(state_filter)]
if region_filter:
    filtered = filtered[filtered['region'].isin(region_filter)]
if position_filter:
    filtered = filtered[filtered['posit'].isin(position_filter)]
if bats_filter:
    filtered = filtered[filtered['Bats'].isin(bats_filter)]
if throws_filter:
    filtered = filtered[filtered['Throws'].isin(throws_filter)]
if name_search:
    filtered = filtered[filtered['firstname'].str.contains(name_search, case=False, na=False) | filtered['lastname'].str.contains(name_search, case=False, na=False)]

# Height and Weight
if filtered['ht'].notna().any():
    filtered = filtered[filtered['ht'].between(ht_range[0], ht_range[1])]
if filtered['WT'].notna().any():
    filtered = filtered[filtered['WT'].between(wt_range[0], wt_range[1])]

# (Rest of filtering: draft, custom stats, etc. same as before)

# (Rest of the app: column selector, export, table, top performers, maps, charts — same as last working version)
