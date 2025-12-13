# Hometown Hot Zones (US Map) — old state heatmap
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

# Pinpoint City Map — shorter, beautiful, with clustering
st.subheader("Hometown Pinpoint Map")
if filtered.empty or 'lat' not in filtered.columns or 'lon' not in filtered.columns:
    st.write("No location data available with current filters.")
else:
    map_data = filtered.dropna(subset=['lat', 'lon']).copy()
    if map_data.empty:
        st.write("No players with hometown coordinates in current view.")
    else:
        map_data['hover_text'] = (
            map_data['firstname'] + " " + map_data['lastname'] + "<br>" +
            map_data['teamName'] + " (" + map_data['year'].astype(str) + ")<br>" +
            map_data['state'] + " | " + map_data['role']
        )

        fig = px.scatter_mapbox(
            map_data,
            lat='lat',
            lon='lon',
            hover_name='hover_text',
            color='role',
            color_discrete_map={'Hitter': '#00D4AA', 'Pitcher': '#FF6B6B'},
            zoom=3,
            height=520,
            title="Player Hometowns — Zoom & Hover for Details"
        )
        
        fig.update_layout(
            mapbox_style="carto-darkmatter",
            margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor='#0E1117',
            paper_bgcolor='#0E1117',
            font_color='white',
            legend_title_text='Role'
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Players by State — your exact current version with % and top schools
st.subheader("Players by State")
if filtered.empty:
    st.write("No data matches current filters.")
else:
    grouped = filtered.groupby(['state', 'teamName']).size().reset_index(name='count')
    
    def top_n_plus_other(g):
        if len(g) <= 5:
            return g
        top4 = g.nlargest(4, 'count')
        other_count = g['count'].sum() - top4['count'].sum()
        other = pd.DataFrame([{'state': g.name, 'teamName': 'Other', 'count': other_count}])
        return pd.concat([top4, other], ignore_index=True)
    
    grouped = grouped.groupby('state').apply(top_n_plus_other).reset_index(drop=True)
    
    state_totals = grouped.groupby('state')['count'].sum().reset_index()
    state_totals['pct'] = (state_totals['count'] / len(filtered) * 100).round(1)
    
    top15_states = state_totals.nlargest(15, 'count')['state'].tolist()
    grouped = grouped[grouped['state'].isin(top15_states)]
    
    grouped['state'] = pd.Categorical(grouped['state'], categories=top15_states, ordered=True)
    grouped = grouped.sort_values(['state', 'count'], ascending=[True, False])
    
    state_labels = {s: f"{s} ({state_totals.loc[state_totals['state']==s, 'pct'].iloc[0]}%)" for s in top15_states}
    grouped['state_label'] = grouped['state'].map(state_labels)
    
    fig = px.bar(grouped, x='count', y='state_label', color='teamName', orientation='h',
                 height=700, hover_data={'count': True})
    fig.update_layout(barmode='stack', yaxis_title="", xaxis_title="Number of Players",
                      legend_title="Team", plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                      font_color='white', showlegend=True,
                      legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02))
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
st.subheader("Players by Team")
if not filtered.empty:
    team_counts = filtered['teamName'].value_counts().reset_index()
    team_counts.columns = ['teamName', 'count']
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(team_counts.head(20), values='count', names='teamName', title='Top 20 Teams by Player Count (%)'), use_container_width=True)
    with col2:
        st.plotly_chart(px.bar(team_counts.head(30).sort_values('count', ascending=False), x='teamName', y='count', color='teamName', title='Top 30 Teams by Player Count'), use_container_width=True)

# State Recruiting Breakdown by Conference Tier
st.subheader("State Recruiting Breakdown by Conference Tier")
if filtered.empty:
    st.write("No data matches current filters.")
else:
    col_left, col_right = st.columns(2)
    with col_left:
        breakdown = filtered.groupby(['state', 'conference_type']).size().unstack(fill_value=0)
        for col in ['Power Conference', 'Mid Major', 'Low Major']:
            if col not in breakdown.columns:
                breakdown[col] = 0
        breakdown = breakdown.rename(columns={'Power Conference': 'Power'})
        breakdown = breakdown[['Power', 'Mid Major', 'Low Major']]
        breakdown['Total'] = breakdown.sum(axis=1)
        breakdown['% Power'] = (breakdown['Power'] / breakdown['Total'] * 100).round(1)
        breakdown = breakdown.sort_values('% Power', ascending=False).head(10)
        display_table = breakdown.copy()
        display_table['% Power'] = display_table['% Power'].astype(str) + '%'
        st.dataframe(
            display_table.style.set_properties(**{'text-align': 'center'}).set_table_styles([
                {'selector': 'th', 'props': 'text-align: center;'}
            ]),
            use_container_width=True,
            hide_index=False,
            height=420
        )
    with col_right:
        conf_counts = filtered['conference_type'].value_counts()
        conf_counts = conf_counts.reindex(['Power Conference', 'Mid Major', 'Low Major'], fill_value=0)
        conf_counts = conf_counts.rename({'Power Conference': 'Power'})
        fig = px.pie(
            names=conf_counts.index,
            values=conf_counts.values,
            color_discrete_sequence=['#00D4AA', '#6C757D', '#DC3545'],
            height=420
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=False,
                          plot_bgcolor='#0E1117', paper_bgcolor='#0E1117', font_color='white')
        st.plotly_chart(fig, use_container_width=True)

# Top Performers
st.subheader("Top Performers (within current filters)")
def make_leaderboard(title, df, stat_col, min_qual_col=None, min_qual_value=None, ascending=False):
    if min_qual_col and min_qual_value:
        df = df[df[min_qual_col] >= min_qual_value]
    if df.empty:
        st.write(f"**{title}** — No players qualify")
        return
    top = df.nlargest(50, stat_col) if not ascending else df.nsmallest(50, stat_col)
    top = top[['firstname','lastname','teamName','year','state',stat_col]].copy()
    top = top.reset_index(drop=True)
    top.index = top.index + 1
    st.write(f"**{title}**")
    st.dataframe(top, use_container_width=True, hide_index=False, height=240)

if 'OPS' in filtered.columns and 'PA' in filtered.columns:
    hitter_ops = filtered[filtered['role'] == 'Hitter'].copy()
    make_leaderboard("Top 50 Highest OPS Hitters (min 100 PA)", hitter_ops, 'OPS', 'PA', 100)
if 'T90/PA' in filtered.columns and 'PA' in filtered.columns:
    hitter_t90 = filtered[filtered['role'] == 'Hitter'].copy()
    make_leaderboard("Top 50 T90/PA (min 100 PA)", hitter_t90, 'T90/PA', 'PA', 100)
if 'ERA' in filtered.columns and 'IP' in filtered.columns:
    pitcher_era = filtered[filtered['role'] == 'Pitcher'].copy()
    make_leaderboard("Top 50 Lowest ERA Pitchers (min 50 IP)", pitcher_era, 'ERA', 'IP', 50, ascending=True)
if 'SO' in filtered.columns and 'IP' in filtered.columns:
    pitcher_so = filtered[filtered['role'] == 'Pitcher'].copy()
    make_leaderboard("Top 50 Highest Strikeout Pitchers (min 50 IP)", pitcher_so, 'SO', 'IP', 50)
