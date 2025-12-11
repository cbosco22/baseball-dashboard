import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="College Baseball Dashboard", layout="wide")
st.title("College Baseball Player Origins Dashboard")

# ====================== LOAD DATA ======================
@st.cache_data(show_spinner=False)
def load_data():
    pitchers = pd.read_csv('pitchers.csv', low_memory=False)
    hitters = pd.read_csv('hitters.csv', low_memory=False)
    pitchers['role'] = 'Pitcher'
    hitters['role'] = 'Hitter'
    df = pd.concat([pitchers, hitters], ignore_index=True)

    # Clean hsplace
    df[['city', 'state_full']] = df['hsplace'].str.split(',', n=1, expand=True)
    df['state_full'] = df['state_full'].str.strip()
    df['city'] = df['city'].str.strip().str.title()

    # State mapping
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

# ====================== SIDEBAR FILTERS (same as before) ======================
# ... (keep all the filters from the last version — league, team, role, year, drafted, games, region)

# (Copy the filter code from the previous message — it's unchanged)

# ====================== PINPOINT MAP (fixed & beautiful) ====================
# (Assume this is after all filters and sort code, where filtered_data is defined)

st.subheader(f"Player High School Locations • {len(filtered_data):,} players")

if not filtered_data.empty:
    # Temporary fallback to state heatmap (since no lat/lon yet; fixes TypeError)
    state_counts = filtered_data.groupby('state').size().reset_index(name='player_count')
    fig = px.choropleth(
        state_counts,
        locations='state',
        locationmode='USA-states',
        color='player_count',
        scope='usa',
        color_continuous_scale='Reds',
        labels={'player_count': 'Player Count'},
        title='Hot Zones by State'
    )
    st.plotly_chart(fig)
else:
    st.write("No data matches filters.")

# ====================== Recruitment Patterns Chart (unchanged) ===============
st.subheader("Recruitment Patterns (Top States per Team)")
if not filtered_data.empty:
    top_states = filtered_data.groupby(['teamName', 'state']).size().reset_index(name='count').sort_values('count', ascending=False).head(20)
    fig_bar = px.bar(top_states, x='state', y='count', color='teamName', title='Top Recruiting States')
    st.plotly_chart(fig_bar)
else:
    st.write("No data matches filters.")
