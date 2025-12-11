import streamlit as st
import pandas as pd
import plotly.express as px

st.title("College Baseball Player Hometowns & Recruitment Dashboard")

@st.cache_data
def load_data():
    pitchers = pd.read_csv('pitchers.csv')
    hitters = pd.read_csv('hitters.csv')
    pitchers['role'] = 'Pitcher'
    hitters['role'] = 'Hitter'
    data = pd.concat([pitchers, hitters], ignore_index=True)
    
    # Parse city and state from hsplace (e.g., "City, ST")
    data[['city', 'state']] = data['hsplace'].str.split(',', n=1, expand=True)
    data['city'] = data['city'].str.strip() if 'city' in data else None
    data['state'] = data['state'].str.strip().str.upper() if 'state' in data else None
    
    # For pinpoint map: We'll use a simple placeholder for lat/lon until we geocode (next step if needed)
    # For now, use a basic city->lat/lon mapping for major cities (expandable)
    # This is a small dict for demo; we can make it full later
    city_to_latlon = {
        "Los Angeles": (34.05, -118.25), "Houston": (29.76, -95.37), "New York": (40.71, -74.01),
        "Chicago": (41.88, -87.63), "Phoenix": (33.45, -112.07), "Miami": (25.76, -80.19),
        # Add more as needed or switch to full geocoding
    }
    data['lat'] = data['city'].map(lambda c: city_to_latlon.get(c.strip(), (None, None))[0])
    data['lon'] = data['city'].map(lambda c: city_to_latlon.get(c.strip(), (None, None))[1])
    
    return data

data = load_data()

# Sidebar Filters
st.sidebar.header("Filters")
role_filter = st.sidebar.multiselect("Role", ['Pitcher', 'Hitter'], default=['Pitcher', 'Hitter'])
league_filter = st.sidebar.multiselect("League (leave blank for all)", data['LeagueAbbr'].unique())
team_filter = st.sidebar.multiselect("Team/School (leave blank for all)", data['teamName'].unique())
year_range = st.sidebar.slider("Year Range", int(data['year'].min()), int(data['year'].max()), (int(data['year'].min()), int(data['year'].max())))

# Make filters optional
filtered_data = data[
    data['role'].isin(role_filter) &
    data['year'].between(year_range[0], year_range[1])
]
if league_filter:
    filtered_data = filtered_data[filtered_data['LeagueAbbr'].isin(league_filter)]
if team_filter:
    filtered_data = filtered_data[filtered_data['teamName'].isin(team_filter)]

# Player table
st.subheader(f"Filtered Players ({len(filtered_data):,} rows)")
st.dataframe(filtered_data)

# Pinpoint Map - Dynamic with clustering for large data
st.subheader(f"Player High School Locations • {len(filtered_data):,} players")
if not filtered_data.empty and filtered_data['lat'].notna().any():
    fig = px.scatter_map(
        filtered_data.dropna(subset=['lat', 'lon']),
        lat='lat', lon='lon',
        hover_name=filtered_data['firstname'] + " " + filtered_data['lastname'],
        hover_data={'teamName': True, 'year': True, 'city': True, 'state': True, 'lat': False, 'lon': False},
        color='role',
        color_discrete_map={'Pitcher': 'red', 'Hitter': 'blue'},
        zoom=3,
        height=600,
        cluster=True,  # Clusters pins when zoomed out - handles thousands of points
        title="High School Pinpoints (clustered when zoomed out)"
    )
    fig.update_layout(map_style="carto-positron")  # Clean modern look like your old Google map
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No geocoded locations available yet for these players. Falling back to state heatmap.")
    state_counts = filtered_data.groupby('state').size().reset_index(name='count')
    fig_state = px.choropleth(state_counts, locations='state', locationmode='USA-states', color='count',
                              scope='usa', color_continuous_scale='Blues')
    st.plotly_chart(fig_state)

# Recruitment Chart
st.subheader("Top Recruiting States")
if not filtered_data.empty:
    top_states = filtered_data['state'].value_counts().head(15).reset_index()
    top_states.columns = ['state', 'count']
    fig_bar = px.bar(top_states, x='state', y='count', color='state', title="Players by State")
    st.plotly_chart(fig_bar)
