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

    # T90s and T90/PA - ONLY for hitters (pitchers get NaN → grayed out in table)
    df['T90s'] = np.nan
    df['T90/PA'] = np.nan

    hitter_mask = df['role'] == 'Hitter'
    if hitter_mask.any():
        df.loc[hitter_mask, 'Singles'] = df.loc[hitter_mask, 'H'] - df.loc[hitter_mask, 'Dbl'] - df.loc[hitter_mask, 'Tpl'] - df.loc[hitter_mask, 'HR']
        df.loc[hitter_mask, 'Singles'] = df.loc[hitter_mask, 'Singles'].fillna(0)
        df.loc[hitter_mask, 'TotalBases'] = df.loc[hitter_mask, 'Singles'] + 2*df.loc[hitter_mask, 'Dbl'].fillna(0) + 3*df.loc[hitter_mask, 'Tpl'].fillna(0) + 4*df.loc[hitter_mask, 'HR'].fillna(0)
        df.loc[hitter_mask, 'T90s'] = df.loc[hitter_mask, 'TotalBases'] + df.loc[hitter_mask, 'SB'].fillna(0) + df.loc[hitter_mask, 'BB'].fillna(0) + df.loc[hitter_mask, 'HBP'].fillna(0)
        df.loc[hitter_mask, 'PA'] = df.loc[hitter_mask, 'AB'].fillna(0) + df.loc[hitter_mask, 'BB'].fillna(0) + df.loc[hitter_mask, 'HBP'].fillna(0) + df.loc[hitter_mask, 'SF'].fillna(0) + df.loc[hitter_mask, 'SH'].fillna(0)
        df.loc[hitter_mask, 'T90/PA'] = df.loc[hitter_mask, 'T90s'] / df.loc[hitter_mask, 'PA'].replace(0, np.nan)

    # Clean Bats and Throws
    df['Bats'] = df['Bats'].str.upper().replace('B', 'S')
    df['Throws'] = df['Throws'].str.upper()

    # Clean and standardize position
    df['posit'] = df['posit'].str.upper().str.strip()

    # Fix Miami / Miami-Ohio
    df.loc[(df['teamName'] == 'Miami') & (df['LeagueAbbr'] == 'MAC'), 'teamName'] = 'Miami-Ohio'

    return df

data = load_data()

# Sidebar Filters
role_filter = st.sidebar.multiselect("Role", ['Pitcher','Hitter'], default=['Pitcher','Hitter'], key="role")
league_filter = st.sidebar.multiselect("League (blank = ALL)", sorted(data['LeagueAbbr'].unique()), key="league")
team_filter = st.sidebar.multiselect("Team/School (blank = ALL)", sorted(data['teamName'].unique()), key="team")
# Default to 2015–2025 for fast initial load
default_start = max(int(data['year'].min()), 2015)
default_end = int(data['year'].max())
year_filter = st.sidebar.slider(
    "Year Range",
    int(data['year'].min()),
    int(data['year'].max()),
    (default_start, default_end),
    key="year"
)
state_filter = st.sidebar.multiselect("State (blank = ALL)", sorted(data['state'].unique()), key="state")
region_filter = st.sidebar.multiselect("Region (blank = ALL)", sorted(data['region'].unique()), key="region")
# Default min games to 5 for reasonable initial view
min_games = st.sidebar.slider("Minimum Games Played", 0, int(data['G'].max()), 5, key="min_games")

# Position filter
position_filter = st.sidebar.multiselect("Position", options=sorted(data['posit'].dropna().unique()), key="posit")

# Bats and Throws
bats_filter = st.sidebar.multiselect("Bats", options=['L', 'R', 'S'], key="bats")
throws_filter = st.sidebar.multiselect("Throws", options=['L', 'R'], key="throws")

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
available_stats = ['ERA', 'OPS', 'W', 'L', 'SO', 'BB', 'HR', 'RBI', 'SB', 'CS', 'Bavg', 'Slg', 'obp', 'WHIP', 'IP', 'H', 'R', 'ER', 'G', 'GS', 'T90s', 'T90/PA']

stat1 = st.sidebar.selectbox("Custom Stat Filter 1", options=['None'] + available_stats, index=0, key="stat1")
filter1_applied = stat1 != 'None'
if filter1_applied:
    direction1 = st.sidebar.radio(f"{stat1} comparison", options=["Greater than or equal to", "Less than or equal to"], key="dir1")
    step1 = 0.1 if stat1 in ['ERA', 'OPS', 'Bavg', 'Slg', 'obp', 'WHIP', 'T90/PA'] else 1.0
    value1 = st.sidebar.number_input(f"{stat1} value", value=0.0, step=step1, key="val1")

stat2 = 'None'
if filter1_applied:
    remaining = [s for s in available_stats if s != stat1]
    stat2 = st.sidebar.selectbox("Custom Stat Filter 2", options=['None'] + remaining, index=0, key="stat2")
if stat2 != 'None':
    direction2 = st.sidebar.radio(f"{stat2} comparison", options=["Greater than or equal to", "Less than or equal to"], key="dir2")
    step2 = 0.1 if stat2 in ['ERA', 'OPS', 'Bavg', 'Slg', 'obp', 'WHIP', 'T90/PA'] else 1.0
    value2 = st.sidebar.number_input(f"{stat2} value", value=0.0, step=step2, key="val2")

# Base filtering
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

# Column selector in expander
with st.expander("Columns to show (click to expand)", expanded=False):
    default_cols = ['lastname', 'firstname', 'teamName', 'year', 'Age', 'state', 'LeagueAbbr', 'experience', 'G', 'T90s', 'OPS', 'draft_Round', 'ERA', 'W', 'SV', 'IP', 'WHIP']
    available_default = [c for c in default_cols if c in filtered.columns]
    cols = st.multiselect("", options=filtered.columns.tolist(), default=available_default, key="cols")

# Export button
csv = filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Export Filtered Data as CSV",
    data=csv,
    file_name='college_baseball_filtered.csv',
    mime='text/csv'
)

st.subheader(f"Filtered Players – {len(filtered):,} rows")

# Single table with horizontal scroll
display_df = filtered[cols] if cols else filtered.head(100)
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

# State map with dark background
st.subheader("Hometown Hot Zones (US Map)")
if not filtered.empty:
    state_counts = filtered.groupby('state').size().reset_index(name='player_count')
    fig_map = px.choropleth(
        state_counts,
        locations='state',
        locationmode='USA-states',
        color='player_count',
        scope='usa',
        color_continuous_scale='Reds',
        title='Hot Zones by State'
    )
    fig_map.update_layout(
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        font_color='white',
        geo_bgcolor='#0E1117'
    )
    st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False})
else:
    st.write("No data matches filters.")

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

# Top Performers (at bottom, with minimum requirements, new layout, new SO table)
st.subheader("Top Performers (within current filters)")

# Hitter tables on top row
hitter_col1, hitter_col2 = st.columns(2)

with hitter_col1:
    if 'OPS' in filtered.columns and 'PA' in filtered.columns:
        ops_qual = filtered[(filtered['role'] == 'Hitter') & (filtered['PA'] >= 100)]
        if not ops_qual.empty:
            top_ops = ops_qual.nlargest(50, 'OPS')[['firstname', 'lastname', 'teamName', 'year', 'OPS', 'PA', 'G']]
            top_ops = top_ops.reset_index(drop=True)
            top_ops.index = top_ops.index + 1
            st.write("**Top 50 Highest OPS Hitters (min 100 PA)**")
            st.dataframe(top_ops, use_container_width=True, hide_index=False)
        else:
            st.write("**No hitters qualify (min 100 PA)**")

with hitter_col2:
    if 'T90/PA' in filtered.columns and 'PA' in filtered.columns:
        t90_qual = filtered[(filtered['role'] == 'Hitter') & (filtered['PA'] >= 100)]
        if not t90_qual.empty:
            top_t90 = t90_qual.nlargest(50, 'T90/PA')[['firstname', 'lastname', 'teamName', 'year', 'T90/PA', 'T90s', 'PA']]
            top_t90 = top_t90.reset_index(drop=True)
            top_t90.index = top_t90.index + 1
            st.write("**Top 50 T90/PA (min 100 PA)**")
            st.dataframe(top_t90, use_container_width=True, hide_index=False)
        else:
            st.write("**No players qualify (min 100 PA)**")

# Pitcher tables on bottom row
pitcher_col1, pitcher_col2 = st.columns(2)

with pitcher_col1:
    if 'ERA' in filtered.columns and 'IP' in filtered.columns:
        era_qual = filtered[(filtered['role'] == 'Pitcher') & (filtered['IP'] >= 50)]
        if not era_qual.empty:
            top_era = era_qual.nsmallest(50, 'ERA')[['firstname', 'lastname', 'teamName', 'year', 'ERA', 'IP', 'G']]
            top_era = top_era.reset_index(drop=True)
            top_era.index = top_era.index + 1
            st.write("**Top 50 Lowest ERA Pitchers (min 50 IP)**")
            st.dataframe(top_era, use_container_width=True, hide_index=False)
        else:
            st.write("**No pitchers qualify (min 50 IP)**")

with pitcher_col2:
    if 'SO' in filtered.columns and 'IP' in filtered.columns:
        so_qual = filtered[(filtered['role'] == 'Pitcher') & (filtered['IP'] >= 50)]
        if not so_qual.empty:
            top_so = so_qual.nlargest(50, 'SO')[['firstname', 'lastname', 'teamName', 'year', 'SO', 'IP', 'G']]
            top_so = top_so.reset_index(drop=True)
            top_so.index = top_so.index + 1
            st.write("**Top 50 Highest Strikeout Pitchers (min 50 IP)**")
            st.dataframe(top_so, use_container_width=True, hide_index=False)
        else:
            st.write("**No pitchers qualify (min 50 IP)**")
