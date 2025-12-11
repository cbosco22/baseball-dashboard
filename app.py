import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="College Baseball Dashboard", layout="wide")
st.title("College Baseball Player Origins Dashboard")

# ====================== LOAD DATA ======================
@st.cache_data(show_spinner=False)
def load_data():
    pitchers = pd.read_csv('pitchers.csv')
    hitters = pd.read_csv('hitters.csv')
    pitchers['role'] = 'Pitcher'
    hitters['role'] = 'Hitter'
    df = pd.concat([pitchers, hitters], ignore_index=True)

    # Clean hsplace: split into city and state
    df[['city', 'state_full']] = df['hsplace'].str.split(',', n=1, expand=True)
    df['state_full'] = df['state_full'].str.strip()
    df['city'] = df['city'].str.strip().str.title()

    # Map full state names to abbreviations
    state_map = {
        'California': 'CA', 'Texas': 'TX', 'Florida': 'FL', 'Georgia': 'GA', 'New York': 'NY',
        'North Carolina': 'NC', 'Illinois': 'IL', 'Pennsylvania': 'PA', 'Ohio': 'OH', 'Michigan': 'MI',
        'Virginia': 'VA', 'Tennessee': 'TN', 'New Jersey': 'NJ', 'South Carolina': 'SC', 'Alabama': 'AL',
        'Louisiana': 'LA', 'Missouri': 'MO', 'Arizona': 'AZ', 'Colorado': 'CO', 'Oregon': 'OR',
        'Nevada': 'NV', 'Washington': 'WA', 'Massachusetts': 'MA', 'Maryland': 'MD', 'Kentucky': 'KY',
        'Oklahoma': 'OK', 'Arkansas': 'AR', 'Indiana': 'IN', 'Mississippi': 'MS', 'Wisconsin': 'WI',
        'Minnesota': 'MN', 'Iowa': 'IA', 'Kansas': 'KS', 'Nebraska': 'NE', 'Idaho': 'ID', 'Utah': 'UT',
        'New Mexico': 'NM', 'West Virginia': 'WV', 'Hawaii': 'HI', 'Alaska': 'AK', 'Connecticut': 'CT',
        'Rhode Island': 'RI', 'Maine': 'ME', 'New Hampshire': 'NH', 'Vermont': 'VT', 'Delaware': 'DE',
        'South Dakota': 'SD', 'North Dakota': 'ND', 'Montana': 'MT', 'Wyoming': 'WY'
    }
    df['state'] = df['state_full'].map(state_map).fillna(df['state_full'])

    return df

df = load_data()

# ====================== SIDEBAR FILTERS ======================
st.sidebar.header("Filters")

league_options = ['All'] + sorted(df['LeagueAbbr'].dropna().unique().tolist())
team_options = ['All'] + sorted(df['teamName'].dropna().unique().tolist())

selected_league = st.sidebar.multiselect("League", options=league_options, default='All')
selected_team = st.sidebar.multiselect("School / Team", options=team_options, default='All')
selected_role = st.sidebar.multiselect("Role", options=['Pitcher', 'Hitter'], default=['Pitcher', 'Hitter'])

year_range = st.sidebar.slider("Year Range", int(df['year'].min()), int(df['year'].max()),
                               (int(df['year'].min()), int(df['year'].max())))

# New filters
only_drafted = st.sidebar.checkbox("Only Drafted Players", value=False)
if only_drafted:
    min_round, max_round = st.sidebar.slider("Draft Round Range", 1, 50, (1, 20), step=1)

min_games = st.sidebar.slider("Minimum Games Played", 0, 200, 0)

# Region filter
regions = {
    "New England": ["CT", "MA", "ME", "NH", "RI", "VT"],
    "Mid Atlantic": ["NJ", "NY", "PA"],
    "South": ["AL", "AR", "FL", "GA", "KY", "LA", "MS", "NC", "SC", "TN", "VA", "WV"],
    "Midwest I": ["IL", "IN", "MI", "OH", "WI"],
    "Midwest II": ["IA", "KS", "MO", "NE", "ND", "SD", "MN"],
    "Southwest": ["AZ", "NM", "OK", "TX"],
    "West": ["AK", "CA", "CO", "HI", "ID", "MT", "NV", "OR", "UT", "WA", "WY"]
}
region_list = ["All"] + list(regions.keys())
selected_region = st.sidebar.multiselect("Region", options=region_list, default="All")

# ====================== APPLY FILTERS ======================
filtered = df.copy()

if 'All' not in selected_league:
    filtered = filtered[filtered['LeagueAbbr'].isin(selected_league)]
if 'All' not in selected_team:
    filtered = filtered[filtered['teamName'].isin(selected_team)]
filtered = filtered[filtered['role'].isin(selected_role)]
filtered = filtered[filtered['year'].between(year_range[0], year_range[1])]

if only_drafted:
    filtered = filtered[filtered['draft_year'].notna()]
    filtered = filtered[filtered['draft_Round'].between(min_round, max_round)]

if 'G' in filtered.columns:
    filtered = filtered[filtered['G'].fillna(0) >= min_games]

if "All" not in selected_region:
    allowed_states = [state for region in selected_region for state in regions[region]]
    filtered = filtered[filtered['state'].isin(allowed_states)]

# ====================== PINPOINT MAP (the one you loved!) ======================
st.subheader(f"Player High School Locations • {len(filtered):,} players")

if not filtered.empty:
    fig = px.scatter_mapbox(
        filtered,
        lat=None, lon=None,
        hover_name=filtered["firstname"] + " " + filtered["lastname"],
        hover_data={"teamName": True, "year": True, "hsplace": True, "role": True},
        color="role",
        color_discrete_map={"Pitcher": "#00FFFF", "Hitter": "#FF6B6B"},
        zoom=3,
        height=700,
        mapbox_style="carto-darkmatter"
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("No players match the current filters.")

# ====================== PLAYER TABLE WITH CUSTOM COLUMNS ======================
st.subheader("Filtered Players")
all_columns = df.columns.tolist()
default_columns = ['firstname', 'lastname', 'year', 'teamName', 'LeagueAbbr', 'hsplace', 'state', 'role', 'Age', 'ht', 'WT', 'posit', 'draft_year', 'draft_Round', 'G', 'ERA', 'OPS']
selected_columns = st.multiselect("Choose columns to show", options=all_columns, default=[c for c in default_columns if c in all_columns])

if selected_columns:
    st.dataframe(filtered[selected_columns].sort_values(["year", "lastname"], ascending=False), use_container_width=True)
else:
    st.dataframe(filtered.sort_values(["year", "lastname"], ascending=False), use_container_width=True)

# ====================== REGION & STATE CHARTS ======================
col1, col2 = st.columns(2)
with col1:
    st.subheader("Players by Region")
    region_counts = filtered.copy()
    region_counts['region'] = 'Other'
    for region, states in regions.items():
        region_counts.loc[region_counts['state'].isin(states), 'region'] = region
    rc = region_counts['region'].value_counts()
    fig_pie = px.pie(values=rc.values, names=rc.index, hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.subheader("Top Recruiting States")
    top_states = filtered['state'].value_counts().head(15)
    fig_bar = px.bar(y=top_states.index, x=top_states.values, orientation='h', color=top_states.values)
    fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)
