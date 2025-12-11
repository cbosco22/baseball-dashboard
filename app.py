import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.title("College Baseball Player Dashboard")

@st.cache_data
def load_data():
    pitchers = pd.read_csv('pitchers.csv')
    hitters = pd.read_csv('hitters.csv')
    pitchers['role'] = 'Pitcher'
    hitters['role'] = 'Hitter'
    all_players = pd.concat([pitchers, hitters], ignore_index=True, sort=False)
    
    # Extract state
    all_players['state'] = all_players['hsplace'].str.split(',').str[-1].str.strip().str.upper()
    us_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
    all_players = all_players[all_players['state'].isin(us_states)]
    
    # Clean draft - fill NaN rounds with 0 for slider logic
    all_players['draft_year'] = pd.to_numeric(all_players['draft_year'], errors='coerce')
    all_players['draft_Round'] = pd.to_numeric(all_players['draft_Round'], errors='coerce').fillna(0)
    all_players['is_drafted'] = all_players['draft_year'].notna()
    
    # Region mapping
    region_map = {
        'East': ['KY', 'OH', 'PA', 'TN', 'WV'],
        'Mid Atlantic': ['DE', 'MD', 'NJ', 'NY', 'VA'],
        'Midwest I': ['IL', 'IN', 'IA', 'KS', 'MI', 'MN', 'MO', 'NE', 'ND', 'SD', 'WI'],
        'Midwest II': ['AR', 'OK', 'TX'],
        'New England': ['CT', 'ME', 'MA', 'NH', 'RI', 'VT'],
        'South': ['AL', 'FL', 'GA', 'LA', 'MS', 'NC', 'SC'],
        'West': ['AK', 'AZ', 'CA', 'CO', 'HI', 'ID', 'MT', 'NV', 'NM', 'OR', 'UT', 'WA', 'WY'],
    }
    def get_region(state):
        for reg, states in region_map.items():
            if state in states:
                return reg
        return 'Other'
    
    all_players['region'] = all_players['state'].apply(get_region)
    
    return all_players

data = load_data()

# Sidebar Filters
st.sidebar.header("Filters")
role_filter = st.sidebar.multiselect("Role", options=['Pitcher', 'Hitter'], default=['Pitcher', 'Hitter'])
league_filter = st.sidebar.multiselect("League (leave blank for ALL)", options=sorted(data['LeagueAbbr'].unique()))
team_filter = st.sidebar.multiselect("Team/School (leave blank for ALL)", options=sorted(data['teamName'].unique()))
year_filter = st.sidebar.slider("Year Range", min_value=int(data['year'].min()), max_value=int(data['year'].max()), value=(int(data['year'].min()), int(data['year'].max())))

state_filter = st.sidebar.multiselect("State (leave blank for ALL)", options=sorted(data['state'].unique()))
region_filter = st.sidebar.multiselect("Region (leave blank for ALL)", options=sorted(data['region'].unique()))

min_games = st.sidebar.slider("Minimum Games Played (G)", min_value=0, max_value=int(data['G'].max()), value=0)

drafted_filter = st.sidebar.radio("Drafted Status", options=["All", "Drafted Only", "Undrafted Only"], index=0)

era_min = st.sidebar.number_input("Min ERA (Pitchers)", value=0.0, step=0.1)
ops_min = st.sidebar.number_input("Min OPS (Hitters)", value=0.0, step=0.1)

# Base filtering
filtered_data = data[
    (data['role'].isin(role_filter)) &
    (data['year'].between(year_filter[0], year_filter[1])) &
    (data['G'] >= min_games)
]
if league_filter:
    filtered_data = filtered_data[filtered_data['LeagueAbbr'].isin(league_filter)]
if team_filter:
    filtered_data = filtered_data[filtered_data['teamName'].isin(team_filter)]
if state_filter:
    filtered_data = filtered_data[filtered_data['state'].isin(state_filter)]
if region_filter:
    filtered_data = filtered_data[filtered_data['region'].isin(region_filter)]

# Draft status
if drafted_filter == "Drafted Only":
    filtered_data = filtered_data[filtered_data['is_drafted']]
elif drafted_filter == "Undrafted Only":
    filtered_data = filtered_data[~filtered_data['is_drafted']]

# Draft round slider - only show if drafted players exist
if filtered_data['is_drafted'].any():
    max_round = int(filtered_data['draft_Round'].max())
    draft_round_range = st.sidebar.slider("Draft Round Range (0 = not drafted)", min_value=0, max_value=max_round, value=(0, max_round))
    filtered_data = filtered_data[filtered_data['draft_Round'].between(draft_round_range[0], draft_round_range[1])]
else:
    st.sidebar.info("No drafted players in current view")

# Stat filters
if 'ERA' in filtered_data.columns:
    filtered_data = filtered_data[(filtered_data['role'] != 'Pitcher') | (filtered_data['ERA'] >= era_min)]
if 'OPS' in filtered_data.columns:
    filtered_data = filtered_data[(filtered_data['role'] != 'Hitter') | (filtered_data['OPS'] >= ops_min)]

# Career view
career_view = st.checkbox("Show Career Aggregated View (one row per player at school)")

if career_view:
    def aggregate_career(df):
        agg_dict = {
            'year': 'nunique',
            'G': 'sum',
            'teamName': 'first',
            'LeagueAbbr': 'first',
            'lastname': 'first',
            'firstname': 'first',
            'hsplace': 'first',
            'state': 'first',
            'region': 'first',
            'is_drafted': 'first',
            'draft_year': 'first',
            'draft_Round': 'first',
            'draft_overall': 'first',
        }
        pitcher_stats = ['W', 'L', 'SO', 'BB', 'IP', 'H', 'R', 'ER', 'HR']
        for stat in pitcher_stats:
            if stat in df.columns:
                agg_dict[stat] = 'sum' if stat in ['W', 'L', 'SO'] else 'mean'
        hitter_stats = ['AB', 'R', 'H', 'Dbl', 'Tpl', 'HR', 'RBI', 'SB', 'CS', 'BB', 'SO']
        for stat in hitter_stats:
            if stat in df.columns:
                agg_dict[stat] = 'sum'
        rate_stats = ['ERA', 'Bavg', 'Slg', 'obp', 'OPS', 'WHIP']
        for stat in rate_stats:
            if stat in df.columns:
                agg_dict[stat] = 'mean'
        
        career = df.groupby(['firstname', 'lastname', 'teamName']).agg(agg_dict).reset_index()
        career['player_name'] = career['firstname'] + " " + career['lastname']
        return career
    
    filtered_data = aggregate_career(filtered_data)

# Sort
sort_stat = st.sidebar.selectbox("Sort Players By", options=['None', 'ERA', 'OPS', 'W', 'SO', 'Bavg', 'G'], index=0)
if sort_stat != 'None':
    ascending = (sort_stat in ['ERA'])
    filtered_data = filtered_data.sort_values(sort_stat, ascending=ascending, na_position='last')

# Custom columns
all_columns = filtered_data.columns.tolist()
default_columns = ['firstname', 'lastname', 'teamName', 'year', 'role', 'G', 'state', 'region', 'draft_Round']
selected_columns = st.multiselect("Choose columns to display in table", options=all_columns, default=default_columns)

st.subheader(f"Filtered Players ({len(filtered_data):,} rows)")
if selected_columns:
    st.dataframe(filtered_data[selected_columns])
else:
    st.dataframe(filtered_data.head(100))

# State map
st.subheader("Hometown Hot Zones (US Map)")
if not filtered_data.empty:
    state_counts = filtered_data.groupby('state').size().reset_index(name='player_count')
    fig_map = px.choropleth(state_counts, locations='state', locationmode='USA-states', color='player_count',
                            scope='usa', color_continuous_scale='Reds', title='Hot Zones by State')
    st.plotly_chart(fig_map)

# Recruitment
st.subheader("Recruitment Patterns (Top States per Team)")
if not filtered_data.empty:
    top_states = filtered_data.groupby(['teamName', 'state']).size().reset_index(name='count').sort_values('count', ascending=False).head(20)
    fig_bar = px.bar(top_states, x='state', y='count', color='teamName', title='Top Recruiting States')
    st.plotly_chart(fig_bar)

# Region graphs
st.subheader("Players by Region")
if not filtered_data.empty:
    region_counts = filtered_data['region'].value_counts().reset_index()
    region_counts.columns = ['region', 'count']
    
    col1, col2 = st.columns(2)
    with col1:
        fig_pie = px.pie(region_counts, values='count', names='region', title='Players by Region (%)')
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        fig_bar_reg = px.bar(region_counts.sort_values('count', ascending=False), x='region', y='count', color='region', title='Player Count by Region')
        st.plotly_chart(fig_bar_reg, use_container_width=True)
