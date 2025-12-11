import streamlit as st
import pandas as pd
import plotly.express as px

st.title("College Baseball Player Dashboard")

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

    return df

data = load_data()

# Sidebar Filters
st.sidebar.header("Filters")
role_filter = st.sidebar.multiselect("Role", ['Pitcher','Hitter'], default=['Pitcher','Hitter'])
league_filter = st.sidebar.multiselect("League (blank = ALL)", sorted(data['LeagueAbbr'].unique()))
team_filter = st.sidebar.multiselect("Team/School (blank = ALL)", sorted(data['teamName'].unique()))
year_filter = st.sidebar.slider("Year Range", int(data['year'].min()), int(data['year'].max()), (int(data['year'].min()), int(data['year'].max())))
state_filter = st.sidebar.multiselect("State (blank = ALL)", sorted(data['state'].unique()))
region_filter = st.sidebar.multiselect("Region (blank = ALL)", sorted(data['region'].unique()))
min_games = st.sidebar.slider("Minimum Games Played", 0, int(data['G'].max()), 0)
drafted_filter = st.sidebar.radio("Drafted Status", ["All", "Drafted Only", "Undrafted Only"])
era_min = st.sidebar.number_input("Min ERA (Pitchers)", value=0.0, step=0.1)
ops_min = st.sidebar.number_input("Min OPS (Hitters)", value=0.0, step=0.1)

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

# Draft round slider — ONLY if drafted players remain after status filter
if filtered['is_drafted'].any():
    max_round = int(filtered['draft_Round'].max())
    draft_round_range = st.sidebar.slider(
        "Draft Round Range (0 = not drafted)",
        min_value=0,
        max_value=max_round,
        value=(0, max_round)
    )
    filtered = filtered[filtered['draft_Round'].between(draft_round_range[0], draft_round_range[1])]
else:
    st.sidebar.info("No drafted players in current view — round filter hidden")

# Stat filters
if 'ERA' in filtered.columns:
    filtered = filtered[(filtered['role'] != 'Pitcher') | (filtered['ERA'] >= era_min)]
if 'OPS' in filtered.columns:
    filtered = filtered[(filtered['role'] != 'Hitter') | (filtered['OPS'] >= ops_min)]

# Career view (kept simple — add back full aggregation if you want)
career_view = st.checkbox("Show Career Aggregated View")
if career_view:
    st.write("Career view not implemented in this version — let me know if you want it back!")

# Sort
sort_by = st.sidebar.selectbox("Sort by", ['None','ERA','OPS','W','SO','Bavg','G'])
if sort_by != 'None':
    asc = sort_by == 'ERA'
    filtered = filtered.sort_values(sort_by, ascending=asc, na_position='last')

# Column selector
default_cols = ['firstname','lastname','teamName','year','role','G','state','region','draft_Round','is_drafted']
cols = st.multiselect("Columns to show", options=filtered.columns.tolist(), default=default_cols)

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

# Region graphs
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
else:
    st.write("No data matches filters.")
