import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.title("College Baseball Player Dashboard")

# Reset button
if st.button("Reset All Filters"):
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

    # Clean height and weight to numeric
    df['ht'] = pd.to_numeric(df['ht'], errors='coerce')
    df['WT'] = pd.to_numeric(df['WT'], errors='coerce')

    return df

data = load_data()

# Sidebar Filters
st.sidebar.header("Filters")

role_filter = st.sidebar.multiselect("Role", ['Pitcher','Hitter'], default=['Pitcher','Hitter'], key="role")
league_filter = st.sidebar.multiselect("League (blank = ALL)", sorted(data['LeagueAbbr'].unique()), key="league")
team_filter = st.sidebar.multiselect("Team/School (blank = ALL)", sorted(data['teamName'].unique()), key="team")
year_filter = st.sidebar.slider("Year Range", int(data['year'].min()), int(data['year'].max()), (int(data['year'].min()), int(data['year'].max())), key="year")
state_filter = st.sidebar.multiselect("State (blank = ALL)", sorted(data['state'].unique()), key="state")
region_filter = st.sidebar.multiselect("Region (blank = ALL)", sorted(data['region'].unique()), key="region")
min_games = st.sidebar.slider("Minimum Games Played", 0, int(data['G'].max()), 0, key="min_games")
drafted_filter = st.sidebar.radio("Drafted Status", ["All", "Drafted Only", "Undrafted Only"], key="drafted")

# Position, Bats, Throws
position_filter = st.sidebar.multiselect("Position", options=sorted(data['posit'].dropna().unique()), key="posit")
bats_filter = st.sidebar.multiselect("Bats", options=sorted(data['Bats'].dropna().unique()), key="bats")
throws_filter = st.sidebar.multiselect("Throws", options=sorted(data['Throws'].dropna().unique()), key="throws")

# Height and Weight sliders (Age removed)
ht_min = int(data['ht'].min()) if data['ht'].notna().any() else 60
ht_max = int(data['ht'].max()) if data['ht'].notna().any() else 80
wt_min = int(data['WT'].min()) if data['WT'].notna().any() else 150
wt_max = int(data['WT'].max()) if data['WT'].notna().any() else 250

ht_range = st.sidebar.slider("Height (inches)", min_value=ht_min, max_value=ht_max, value=(ht_min, ht_max), key="ht")
wt_range = st.sidebar.slider("Weight (lbs)", min_value=wt_min, max_value=wt_max, value=(wt_min, wt_max), key="wt")

# Player name search
name_search = st.sidebar.text_input("Search Player Name", key="name_search")

# Draft round slider
draft_round_range = st.sidebar.slider(
    "Draft Round Range (0 = undrafted, 1+ = drafted round)",
    min_value=0,
    max_value=70,
    value=(0, 70),
    key="draft_round"
)

# Custom Stat Filters
available_stats = ['ERA', 'OPS', 'W', 'L', 'SO', 'BB', 'HR', 'RBI', 'SB', 'CS', 'Bavg', 'Slg', 'obp', 'WHIP', 'IP', 'H', 'R', 'ER', 'G', 'GS', 'T90s', 'T90_per_PA']

stat1 = st.sidebar.selectbox("Custom Stat Filter 1", options=['None'] + available_stats, index=0, key="stat1")
filter1_applied = stat1 != 'None'
if filter1_applied:
    direction1 = st.sidebar.radio(f"{stat1} comparison", options=["Greater than or equal to", "Less than or equal to"], key="dir1")
    step1 = 0.1 if stat1 in ['ERA', 'OPS', 'Bavg', 'Slg', 'obp', 'WHIP', 'T90_per_PA'] else 1.0
    value1 = st.sidebar.number_input(f"{stat1} value", value=0.0, step=step1, key="val1")

stat2 = 'None'
if filter1_applied:
    remaining = [s for s in available_stats if s != stat1]
    stat2 = st.sidebar.selectbox("Custom Stat Filter 2", options=['None'] + remaining, index=0, key="stat2")
if stat2 != 'None':
    direction2 = st.sidebar.radio(f"{stat2} comparison", options=["Greater than or equal to", "Less than or equal to"], key="dir2")
    step2 = 0.1 if stat2 in ['ERA', 'OPS', 'Bavg', 'Slg', 'obp', 'WHIP', 'T90_per_PA'] else 1.0
    value2 = st.sidebar.number_input(f"{stat2} value", value=0.0, step=step2, key="val2")

# Base filtering
filtered = data[
    data['role'].isin(role_filter) &
    data['year'].between(*year_filter) &
    (data['G'] >= min_games) &
    data['ht'].between(ht_range[0], ht_range[1]) &
    data['WT'].between(wt_range[0], wt_range[1])
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

# Draft status filter
if drafted_filter == "Drafted Only":
    filtered = filtered[filtered['is_drafted']]
elif drafted_filter == "Undrafted Only":
    filtered = filtered[~filtered['is_drafted']]

# Draft round filter
filtered = filtered[filtered['draft_Round'].between(draft_round_range[0], draft_round_range[1])]

# Custom stat filters
if stat1 != 'None' and stat1 in filtered.columns:
    if direction1 == "Greater than or equal to":
        filtered = filtered[filtered[stat1] >= value1]
    else:
        filtered = filtered[filtered[stat1] <= value1]

if stat2 != 'None' and stat2 in filtered.columns:
    if direction2 == "Greater than or equal to":
        filtered = filtered[filtered[stat2] >= value2]
    else:
        filtered = filtered[filtered[stat2] <= value2]

# Column selector
default_cols = ['firstname','lastname','teamName','year','role','G','state','region','draft_Round','is_drafted','T90s','T90_per_PA','posit','Bats','Throws','ht','WT']
cols = st.multiselect("Columns to show", options=filtered.columns.tolist(), default=default_cols, key="cols")

# Export button
csv = filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Export Filtered Data as CSV",
    data=csv,
    file_name='college_baseball_filtered.csv',
    mime='text/csv'
)

st.subheader(f"Filtered Players – {len(filtered):,} rows")
st.dataframe(filtered[cols] if cols else filtered.head(100))

# Top Performers
st.subheader("Top Performers (within current filters)")
col1, col2, col3 = st.columns(3)

with col1:
    if 'ERA' in filtered.columns:
        top_era = filtered[filtered['role'] == 'Pitcher'].nsmallest(50, 'ERA')[['firstname', 'lastname', 'teamName', 'year', 'ERA', 'G']]
        st.write("**Top 50 Lowest ERA Pitchers**")
        st.dataframe(top_era)

with col2:
    if 'OPS' in filtered.columns:
        top_ops = filtered[filtered['role'] == 'Hitter'].nlargest(50, 'OPS')[['firstname', 'lastname', 'teamName', 'year', 'OPS', 'G']]
        st.write("**Top 50 Highest OPS Hitters**")
        st.dataframe(top_ops)

with col3:
    if 'T90_per_PA' in filtered.columns:
        top_t90 = filtered.nlargest(50, 'T90_per_PA')[['firstname', 'lastname', 'teamName', 'year', 'T90_per_PA', 'T90s', 'PA']]
        st.write("**Top 50 T90 per PA**")
        st.dataframe(top_t90)

# State map
st.subheader("Hometown Hot Zones (US Map)")
if not filtered.empty:
    state_counts = filtered.groupby('state').size().reset_index(name='player_count')
    fig_map = px.choropleth(state_counts, locations='state', locationmode='USA-states', color='player_count',
                            scope='usa', color_continuous_scale='Reds', title='Hot Zones by State')
    st.plotly_chart(fig_map, use_container_width=True)

# Recruitment patterns
st.subheader("Recruitment Patterns (Top States per Team)")
if not filtered.empty:
    top_states = filtered.groupby(['teamName', 'state']).size().reset_index(name='count').sort_values('count', ascending=False).head(20)
    fig_bar = px.bar(top_states, x='state', y='count', color='teamName', title='Top Recruiting States')
    st.plotly_chart(fig_bar, use_container_width=True)

# Players by Region
st.subheader("Players by Region")
if not filtered.empty:
    region_counts = filtered['region'].value_counts().reset_index()
    region_counts.columns = ['region', 'count']
    col1, col2 = st.columns(2)
    with col1:
        fig_pie = px.pie(region_counts, values='count', names='region', title='Players by Region (%)')
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        fig_bar_reg = px.bar(region_counts.sort_values('count', ascending=False), x='region', y='count', color='region', title='Player Count by Region')
        st.plotly_chart(fig_bar_reg, use_container_width=True)

# Players by Team
st.subheader("Players by Team (within current filters)")
if not filtered.empty:
    team_counts = filtered['teamName'].value_counts().reset_index()
    team_counts.columns = ['teamName', 'count']
    
    col1, col2 = st.columns(2)
    with col1:
        fig_pie_team = px.pie(team_counts.head(20), values='count', names='teamName', title='Top 20 Teams by Player Count (%)')
        st.plotly_chart(fig_pie_team, use_container_width=True)
    with col2:
        fig_bar_team = px.bar(team_counts.head(30).sort_values('count', ascending=False), x='teamName', y='count', color='teamName', title='Top 30 Teams by Player Count')
        st.plotly_chart(fig_bar_team, use_container_width=True)
else:
    st.write("No data matches filters.")
