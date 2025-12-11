import streamlit as st
import pandas as pd
import plotly.express as px

st.title("College Baseball Player Dashboard")

# Reset button at the top
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

    # Draft cleanup - undrafted = 0
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

# Draft round slider
draft_round_range = st.sidebar.slider(
    "Draft Round Range (0 = undrafted, 1+ = drafted round)",
    min_value=0,
    max_value=70,
    value=(0, 70),
    key="draft_round"
)

# Available stats for custom filters
available_stats = ['ERA', 'OPS', 'W', 'L', 'SO', 'BB', 'HR', 'RBI', 'SB', 'CS', 'Bavg', 'Slg', 'obp', 'WHIP', 'IP', 'H', 'R', 'ER', 'G', 'GS']

# Custom Stat Filter 1
stat1 = st.sidebar.selectbox("Custom Stat Filter 1", options=['None'] + available_stats, index=0, key="stat1")
filter1_applied = stat1 != 'None'
if filter1_applied:
    direction1 = st.sidebar.radio(f"{stat1} comparison", options=["Greater than or equal to", "Less than or equal to"], key="dir1")
    step1 = 0.1 if stat1 in ['ERA', 'OPS', 'Bavg', 'Slg', 'obp', 'WHIP'] else 1.0
    value1 = st.sidebar.number_input(f"{stat1} value", value=0.0, step=step1, key="val1")

# Custom Stat Filter 2
stat2 = 'None'
if filter1_applied:
    remaining_stats = [s for s in available_stats if s != stat1]
    stat2 = st.sidebar.selectbox("Custom Stat Filter 2", options=['None'] + remaining_stats, index=0, key="stat2")
if stat2 != 'None':
    direction2 = st.sidebar.radio(f"{stat2} comparison", options=["Greater than or equal to", "Less than or equal to"], key="dir2")
    step2 = 0.1 if stat2 in ['ERA', 'OPS', 'Bavg', 'Slg', 'obp', 'WHIP'] else 1.0
    value2 = st.sidebar.number_input(f"{stat2} value", value=0.0, step=step2, key="val2")

# Base filtering
filtered = data[
    data['role'].isin(role_filter) &
    data['year'].between(*year_filter) &
    (data['G'] >= min_games)
]
for f, col in zip([league_filter, team_filter, state_filter, region_filter],
                  ['LeagueAbbr', 'teamName', 'state', 'region']):
    if f:
        filtered = filtered[filtered[col].isin(f)]

# Draft status filter
if drafted_filter == "Drafted Only":
    filtered = filtered[filtered['is_drafted']]
elif drafted_filter == "Undrafted Only":
    filtered = filtered[~filtered['is_drafted']]

# Draft round filter
filtered = filtered[filtered['draft_Round'].between(draft_round_range[0], draft_round_range[1])]

# Apply custom stat filters
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

# Sort
sort_by = st.sidebar.selectbox("Sort by", ['None','ERA','OPS','W','SO','Bavg','G'], key="sort")
if sort_by != 'None':
    asc = sort_by == 'ERA'
    filtered = filtered.sort_values(sort_by, ascending=asc, na_position='last')

# Column selector
default_cols = ['firstname','lastname','teamName','year','role','G','state','region','draft_Round','is_drafted']
cols = st.multiselect("Columns to show", options=filtered.columns.tolist(), default=default_cols, key="cols")

st.subheader(f"Filtered Players – {len(filtered):,} rows")
st.dataframe(filtered[cols] if cols else filtered.head(100))

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
