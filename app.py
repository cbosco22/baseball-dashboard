import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.title("College Baseball Player Dashboard")

# Reset button
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

    # T90s and T90/PA — only for hitters
    df['T90s'] = np.nan
    df['T90/PA'] = np.nan
    hitter_mask = df['role'] == 'Hitter'
    if hitter_mask.any():
        df.loc[hitter_mask, 'Singles'] = (df.loc[hitter_mask, 'H'] - df.loc[hitter_mask, 'Dbl'] - df.loc[hitter_mask, 'Tpl'] - df.loc[hitter_mask, 'HR']).fillna(0)
        df.loc[hitter_mask, 'TotalBases'] = (df.loc[hitter_mask, 'Singles'] + 2*df.loc[hitter_mask, 'Dbl'].fillna(0) + 3*df.loc[hitter_mask, 'Tpl'].fillna(0) + 4*df.loc[hitter_mask, 'HR'].fillna(0))
        df.loc[hitter_mask, 'T90s'] = (df.loc[hitter_mask, 'TotalBases'] + df.loc[hitter_mask, 'SB'].fillna(0) + df.loc[hitter_mask, 'BB'].fillna(0) + df.loc[hitter_mask, 'HBP'].fillna(0))
        df.loc[hitter_mask, 'PA'] = (df.loc[hitter_mask, 'AB'].fillna(0) + df.loc[hitter_mask, 'BB'].fillna(0) + df.loc[hitter_mask, 'HBP'].fillna(0) + df.loc[hitter_mask, 'SF'].fillna(0) + df.loc[hitter_mask, 'SH'].fillna(0))
        df.loc[hitter_mask, 'T90/PA'] = df.loc[hitter_mask, 'T90s'] / df.loc[hitter_mask, 'PA'].replace(0, np.nan)

    # Clean Bats/Throws/Position
    df['Bats'] = df['Bats'].str.upper().replace('B', 'S')
    df['Throws'] = df['Throws'].str.upper()
    df['posit'] = df['posit'].str.upper().str.strip()

    # Miami → Miami-Ohio fix
    df.loc[(df['teamName'] == 'Miami') & (df['LeagueAbbr'] == 'MAC'), 'teamName'] = 'Miami-Ohio'

    # Conference type
    power = ['Atlantic Coast Conference','Big 12 Conference','Big Ten Conference','Pacific-10 Conference','Pacific-12 Conference','Southeastern Conference']
    low_major = ['Big South Conference','Patriot League','Ivy League','America East Conference','Metro Atlantic Athletic Conference','Northeast Conference','Southwest Athletic Conference','Horizon League']
    df['conference_type'] = 'Mid Major'
    df.loc[df['leagueName'].isin(power), 'conference_type'] = 'Power Conference'
    df.loc[df['leagueName'].isin(low_major), 'conference_type'] = 'Low Major'

    # Academic School flag
    academic_schools = ['Air Force','Army','Boston College','Brown','Bryant','Bryant University','Bucknell','California','Columbia','Cornell','Dartmouth','Davidson','Davidson College','Duke','Fordham','Georgetown','Georgia Tech','Harvard','Holy Cross','Lafayette','Lafayette College','Lehigh','Maryland','Massachusetts','Michigan','Navy','New Jersey Tech','North Carolina','Northeastern','Northwestern','Notre Dame','Penn','Pennsylvania','Princeton','Purdue','Rice','Richmond','Stanford','Tulane','UC Davis','UC Irvine','UC San Diego','UC Santa Barbara','UCLA','USC','Vanderbilt','Villanova','Virginia','Wake Forest','Washington','William and Mary','Wofford','Yale']
    df['is_academic_school'] = df['teamName'].isin(academic_schools)

    return df

data = load_data()

# Filters
year_filter = st.sidebar.slider("Year Range", int(data['year'].min()), int(data['year'].max()), (2015, int(data['year'].max())), key="year")
role_filter = st.sidebar.multiselect("Role", ['Pitcher','Hitter'], default=['Pitcher','Hitter'], key="role")
league_filter = st.sidebar.multiselect("Conference", sorted(data['LeagueAbbr'].unique()), key="league")
conference_type_filter = st.sidebar.multiselect("Conference Type", options=['Power Conference', 'Mid Major', 'Low Major'], key="conference_type")
academic_school_filter = st.sidebar.radio("Academic School", ["All", "Top 60 Academic"], key="academic_school")
team_filter = st.sidebar.multiselect("Team", sorted(data['teamName'].unique()), key="team")
state_filter = st.sidebar.multiselect("State", sorted(data['state'].unique()), key="state")
region_filter = st.sidebar.multiselect("Region", sorted(data['region'].unique()), key="region")

min_games = st.sidebar.slider("Minimum Games Played", 0, int(data['G'].max()), 5, key="min_games")
position_filter = st.sidebar.multiselect("Position", options=sorted(data['posit'].dropna().unique()), key="posit")
bats_filter = st.sidebar.multiselect("Bats", options=['L', 'R', 'S'], key="bats")
throws_filter = st.sidebar.multiselect("Throws", options=['L', 'R'], key="throws")

draft_round_range = st.sidebar.slider("Draft Round Range", 0, 70, (0,70), key="draft_round")

good_players_only = st.sidebar.checkbox("Good Players Only", key="good_players")

available_stats = ['ERA','OPS','W','L','SO','BB','HR','RBI','SB','CS','Bavg','Slg','obp','WHIP','IP','H','R','ER','G','GS','T90s','T90/PA']
stat1 = st.sidebar.selectbox("Custom Stat Filter 1", ['None']+available_stats, key="stat1")
if stat1 != 'None':
    direction1 = st.sidebar.radio(f"{stat1} comparison", ["Greater than or equal to", "Less than or equal to"], key="dir1")
    step1 = 0.1 if stat1 in ['ERA','OPS','Bavg','Slg','obp','WHIP','T90/PA'] else 1.0
    value1 = st.sidebar.number_input(f"{stat1} value", value=0.0, step=step1, key="val1")

stat2 = 'None'
if stat1 != 'None':
    remaining = [s for s in available_stats if s != stat1]
    stat2 = st.sidebar.selectbox("Custom Stat Filter 2", ['None']+remaining, key="stat2")
if stat2 != 'None':
    direction2 = st.sidebar.radio(f"{stat2} comparison", ["Greater than or equal to", "Less than or equal to"], key="dir2")
    step2 = 0.1 if stat2 in ['ERA','OPS','Bavg','Slg','obp','WHIP','T90/PA'] else 1.0
    value2 = st.sidebar.number_input(f"{stat2} value", value=0.0, step=step2, key="val2")

name_search = st.sidebar.text_input("Search Player Name", key="name_search")


# Base filtering
filtered = data[
    data['role'].isin(role_filter) &
    data['year'].between(*year_filter) &
    (data['G'] >= min_games)
]

if league_filter: filtered = filtered[filtered['LeagueAbbr'].isin(league_filter)]
if team_filter: filtered = filtered[filtered['teamName'].isin(team_filter)]
if state_filter: filtered = filtered[filtered['state'].isin(state_filter)]
if region_filter: filtered = filtered[filtered['region'].isin(region_filter)]
if position_filter: filtered = filtered[filtered['posit'].isin(position_filter)]
if bats_filter: filtered = filtered[filtered['Bats'].isin(bats_filter)]
if throws_filter: filtered = filtered[filtered['Throws'].isin(throws_filter)]
if name_search:
    filtered = filtered[filtered['firstname'].str.contains(name_search, case=False, na=False) |
                      filtered['lastname'].str.contains(name_search, case=False, na=False)]

if conference_type_filter:
    filtered = filtered[filtered['conference_type'].isin(conference_type_filter)]
if academic_school_filter == "Academic Schools Only":
    filtered = filtered[filtered['is_academic_school']]

filtered = filtered[filtered['draft_Round'].between(*draft_round_range)]

# Good Players Only filter
if good_players_only:
    # Hitters: >30 G and T90/PA > 0.550
    hitters_good = (filtered['role'] == 'Hitter') & (filtered['G'] > 30) & (filtered['T90/PA'] > 0.550)
    # Pitchers: >30 IP and WHIP < 1.35
    pitchers_good = (filtered['role'] == 'Pitcher') & (filtered['IP'] > 30) & (filtered['WHIP'] < 1.35)
    filtered = filtered[hitters_good | pitchers_good]

# Custom stat filters
if stat1 != 'None' and stat1 in filtered.columns:
    filtered = filtered[filtered[stat1] >= value1] if direction1 == "Greater than or equal to" else filtered[filtered[stat1] <= value1]
if stat2 != 'None' and stat2 in filtered.columns:
    filtered = filtered[filtered[stat2] >= value2] if direction2 == "Greater than or equal to" else filtered[filtered[stat2] <= value2]

# Column selector
with st.expander("Columns to show (click to expand)", expanded=False):
    default_cols = ['lastname','firstname','teamName','year','Age','state','LeagueAbbr','experience','G','T90s','OPS','draft_Round','ERA','W','SV','IP','WHIP']
    available_default = [c for c in default_cols if c in filtered.columns]
    cols = st.multiselect("", options=filtered.columns.tolist(), default=available_default, key="cols")

# Export
csv = filtered.to_csv(index=False).encode('utf-8')
st.download_button("Export Filtered Data as CSV", data=csv, file_name='college_baseball_filtered.csv', mime='text/csv')

st.subheader(f"Filtered Players – {len(filtered):,} rows")
st.dataframe(filtered[cols] if cols else filtered.head(100), use_container_width=True, hide_index=True)

# State map
st.subheader("Hometown Hot Zones (US Map)")
if not filtered.empty:
    state_counts = filtered.groupby('state').size().reset_index(name='player_count')
    fig_map = px.choropleth(state_counts, locations='state', locationmode='USA-states', color='player_count',
                            scope='usa', color_continuous_scale='Reds', title='Hot Zones by State')
    fig_map.update_layout(paper_bgcolor='#0E1117', plot_bgcolor='#0E1117', font_color='white', geo_bgcolor='#0E1117')
    st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False})

# Recruitment Patterns — Top States descending, schools sorted, % next to state
st.subheader("Recruitment Patterns (Top Recruiting States)")

if filtered.empty:
    st.write("No data matches current filters.")
else:
    # Group by state and team
    grouped = filtered.groupby(['state', 'teamName']).size().reset_index(name='count')
    
    # Keep top 4 teams + "Other" per state
    def top_n_plus_other(g):
        if len(g) <= 5:
            return g
        top4 = g.nlargest(4, 'count')
        other_count = g['count'].sum() - top4['count'].sum()
        other = pd.DataFrame([{'state': g.name, 'teamName': 'Other', 'count': other_count}])
        return pd.concat([top4, other], ignore_index=True)
    
    grouped = grouped.groupby('state').apply(top_n_plus_other).reset_index(drop=True)
    
    # Total per state + % of all players
    state_totals = grouped.groupby('state')['count'].sum().reset_index()
    state_totals['pct'] = (state_totals['count'] / len(filtered) * 100).round(1)
    
    # TOP 15 states by total players, descending
    top15_states = state_totals.nlargest(15, 'count')['state'].tolist()
    grouped = grouped[grouped['state'].isin(top15_states)]
    
    # Sort states descending (highest % at top)
    grouped['state'] = pd.Categorical(grouped['state'], categories=top15_states, ordered=True)
    grouped = grouped.sort_values(['state', 'count'], ascending=[True, False])
    
    # Add % to state label
    state_labels = {s: f"{s} ({state_totals.loc[state_totals['state']==s, 'pct'].iloc[0]}%)" for s in top15_states}
    grouped['state_label'] = grouped['state'].map(state_labels)
    
    # Plot
    fig = px.bar(
        grouped,
        x='count',
        y='state_label',
        color='teamName',
        orientation='h',
        title="Top Recruiting States — % of All Players",
        height=700,
        hover_data={'count': True}
    )
    
    fig.update_layout(
        barmode='stack',
        yaxis_title="",
        xaxis_title="Number of Players",
        legend_title="Team",
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117',
        font_color='white',
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Players by Region
st.subheader("Players by Region")
if not filtered.empty:
    region_counts = filtered['region'].value_counts().reset_index()
    region_counts.columns = ['region', 'count']
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(region_counts, values='count', names='region', title='Players by Region (%)'), use_container_width=True)
    with col2:
        st.plotly_chart(px.bar(region_counts.sort_values('count', ascending=False), x='region', y='count', color='region', title='Player Count by Region'), use_container_width=True)

# Players by Team
st.subheader("Players by Team (within current filters)")
if not filtered.empty:
    team_counts = filtered['teamName'].value_counts().reset_index()
    team_counts.columns = ['teamName', 'count']
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(team_counts.head(20), values='count', names='teamName', title='Top 20 Teams by Player Count (%)'), use_container_width=True)
    with col2:
        st.plotly_chart(px.bar(team_counts.head(30).sort_values('count', ascending=False), x='teamName', y='count', color='teamName', title='Top 30 Teams by Player Count'), use_container_width=True)

# Top Performers
st.subheader("Top Performers (within current filters)")
hitter_col1, hitter_col2 = st.columns(2)
with hitter_col1:
    if 'OPS' in filtered.columns and 'PA' in filtered.columns:
        ops_qual = filtered[(filtered['role'] == 'Hitter') & (filtered['PA'] >= 100)]
        if not ops_qual.empty:
            top_ops = ops_qual.nlargest(50, 'OPS')[['firstname','lastname','teamName','year','state','OPS','PA','G']]
            top_ops = top_ops.reset_index(drop=True)
            top_ops.index = top_ops.index + 1
            st.write("**Top 50 Highest OPS Hitters (min 100 PA)**")
            st.dataframe(top_ops, use_container_width=True, hide_index=False)

with hitter_col2:
    if 'T90/PA' in filtered.columns and 'PA' in filtered.columns:
        t90_qual = filtered[(filtered['role'] == 'Hitter') & (filtered['PA'] >= 100)]
        if not t90_qual.empty:
            top_t90 = t90_qual.nlargest(50, 'T90/PA')[['firstname','lastname','teamName','year','state','T90/PA','T90s','PA']]
            top_t90 = top_t90.reset_index(drop=True)
            top_t90.index = top_t90.index + 1
            st.write("**Top 50 T90/PA (min 100 PA)**")
            st.dataframe(top_t90, use_container_width=True, hide_index=False)

pitcher_col1, pitcher_col2 = st.columns(2)
with pitcher_col1:
    if 'ERA' in filtered.columns and 'IP' in filtered.columns:
        era_qual = filtered[(filtered['role'] == 'Pitcher') & (filtered['IP'] >= 50)]
        if not era_qual.empty:
            top_era = era_qual.nsmallest(50, 'ERA')[['firstname','lastname','teamName','year','state','ERA','IP','G']]
            top_era = top_era.reset_index(drop=True)
            top_era.index = top_era.index + 1
            st.write("**Top 50 Lowest ERA Pitchers (min 50 IP)**")
            st.dataframe(top_era, use_container_width=True, hide_index=False)

with pitcher_col2:
    if 'SO' in filtered.columns and 'IP' in filtered.columns:
        so_qual = filtered[(filtered['role'] == 'Pitcher') & (filtered['IP'] >= 50)]
        if not so_qual.empty:
            top_so = so_qual.nlargest(50, 'SO')[['firstname','lastname','teamName','year','state','SO','IP','G']]
            top_so = top_so.reset_index(drop=True)
            top_so.index = top_so.index + 1
            st.write("**Top 50 Highest Strikeout Pitchers (min 50 IP)**")
            st.dataframe(top_so, use_container_width=True, hide_index=False)

# State Conference Breakdown Table
st.subheader("State Recruiting Breakdown by Conference Tier")

if filtered.empty:
    st.write("No data matches current filters.")
else:
    # Count players per state and conference type
    breakdown = filtered.groupby(['state', 'conference_type']).size().unstack(fill_value=0)
    
    # Ensure all three columns exist
    for col in ['Power Conference', 'Mid Major', 'Low Major']:
        if col not in breakdown.columns:
            breakdown[col] = 0
    
    # Reorder columns
    breakdown = breakdown[['Power Conference', 'Mid Major', 'Low Major']]
    
    # Total players per state
    breakdown['Total'] = breakdown.sum(axis=1)
    
    # % of players going Power Conference
    breakdown['% Power Conference'] = (breakdown['Power Conference'] / breakdown['Total'] * 100).round(1)
    
    # Sort by % Power descending
    breakdown = breakdown.sort_values('% Power Conference', ascending=False)
    
    # Format % column
    breakdown_display = breakdown.copy()
    breakdown_display['% Power Conference'] = breakdown_display['% Power Conference'].astype(str) + '%'
    
    st.dataframe(
        breakdown_display,
        use_container_width=True,
        hide_index=False
    )
