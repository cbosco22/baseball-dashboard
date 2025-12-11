import streamlit as st
import pandas as pd
import plotly.express as px

# Title for your web app
st.title("College Baseball Player Dashboard")

# Load the CSVs (this handles large files efficiently)
@st.cache_data  # Caches data to speed up reloads
def load_data():
    pitchers = pd.read_csv('pitchers.csv')
    hitters = pd.read_csv('hitters.csv')
    
    # Add a 'role' column to distinguish
    pitchers['role'] = 'Pitcher'
    hitters['role'] = 'Hitter'
    
    # Merge into one DataFrame (ignores unique columns, keeps common ones)
    all_players = pd.concat([pitchers, hitters], ignore_index=True)
    
    # Parse hometowns: Assume 'hsplace' is like 'City,State' – extract state
    all_players['state'] = all_players['hsplace'].str.split(',').str[-1].str.strip().str.upper()  # Uppercase for consistency (e.g., 'CA')
    
    # Filter to valid US states (optional: add more if needed)
    us_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
    all_players = all_players[all_players['state'].isin(us_states)]
    
    return all_players

data = load_data()

# Sidebar for filters
st.sidebar.header("Filters")
role_filter = st.sidebar.multiselect("Role", options=['Pitcher', 'Hitter'], default=['Pitcher', 'Hitter'])
league_filter = st.sidebar.multiselect("League", options=data['LeagueAbbr'].unique())
team_filter = st.sidebar.multiselect("Team/School", options=data['teamName'].unique())
year_filter = st.sidebar.slider("Year Range", min_value=int(data['year'].min()), max_value=int(data['year'].max()), value=(int(data['year'].min()), int(data['year'].max())))

# Stat filters (examples; add more as needed)
if 'Pitcher' in role_filter:
    era_min = st.sidebar.number_input("Min ERA (Pitchers)", value=0.0, step=0.1)
else:
    era_min = 0.0  # Default if no pitchers

if 'Hitter' in role_filter:
    ops_min = st.sidebar.number_input("Min OPS (Hitters)", value=0.0, step=0.1)
else:
    ops_min = 0.0

# Apply filters (default to all if nothing selected)
if not league_filter:
    league_filter = data['LeagueAbbr'].unique()
if not team_filter:
    team_filter = data['teamName'].unique()

filtered_data = data[
    (data['role'].isin(role_filter)) &
    (data['LeagueAbbr'].isin(league_filter)) &
    (data['teamName'].isin(team_filter)) &
    (data['year'].between(year_filter[0], year_filter[1]))
]

# Stat-based filtering
if 'ERA' in filtered_data.columns:
    filtered_data = filtered_data[(filtered_data['role'] != 'Pitcher') | (filtered_data['ERA'] >= era_min)]
if 'OPS' in filtered_data.columns:
    filtered_data = filtered_data[(filtered_data['role'] != 'Hitter') | (filtered_data['OPS'] >= ops_min)]

# Sort by a stat (example: select one to sort by)
sort_stat = st.sidebar.selectbox("Sort Players By", options=['None', 'ERA', 'OPS', 'W', 'SO', 'Bavg'], index=0)
if sort_stat != 'None':
    ascending = (sort_stat in ['ERA'])  # Ascending for ERA (lower better)
    filtered_data = filtered_data.sort_values(sort_stat, ascending=ascending)

# Display filtered player list (top 100 for performance)
st.subheader("Filtered Players")
st.dataframe(filtered_data.head(100))  # Show table; exportable via Streamlit

# Map: Hot zones by state (choropleth heatmap fallback, since no lat/lon yet)
st.subheader("Hometown Hot Zones (US Map)")
if not filtered_data.empty:
    try:
        state_counts = filtered_data.groupby('state').size().reset_index(name='player_count')
        fig_map = px.choropleth(state_counts, locations='state', locationmode='USA-states', color='player_count',
                                scope='usa', color_continuous_scale='Reds', labels={'player_count': 'Player Count'},
                                title='Hot Zones by State')
        st.plotly_chart(fig_map)
    except Exception as e:
        st.error(f"Map error: {str(e)}. Falling back to basic display.")
        st.write("No geo data available yet—showing state counts table instead.")
        st.dataframe(state_counts)
else:
    st.write("No data matches filters.")

# Chart: Top states for selected teams (bar chart)
st.subheader("Recruitment Patterns (Top States per Team)")
if not filtered_data.empty:
    top_states = filtered_data.groupby(['teamName', 'state']).size().reset_index(name='count').sort_values('count', ascending=False).head(20)
    fig_bar = px.bar(top_states, x='state', y='count', color='teamName', title='Top Recruiting States')
    st.plotly_chart(fig_bar)
else:
    st.write("No data matches filters.")
