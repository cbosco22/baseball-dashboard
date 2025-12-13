# ... (all your previous code up to the export button and filtered players table remains the same)

# Hometown Hot Zones (US Map) — the old state heatmap
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

# Pinpoint City Map — shorter height
st.subheader("Hometown Pinpoint Map")

if filtered.empty or 'lat' not in filtered.columns or 'lon' not in filtered.columns:
    st.write("No location data available with current filters.")
else:
    map_data = filtered.dropna(subset=['lat', 'lon']).copy()
    if map_data.empty:
        st.write("No players with hometown coordinates in current view.")
    else:
        map_data['hover_text'] = map_data['firstname'] + " " + map_data['lastname'] + "<br>" + \
                                 map_data['teamName'] + " (" + map_data['year'].astype(str) + ")<br>" + \
                                 map_data['state'] + " | " + map_data['role']

        fig = px.scatter_mapbox(
            map_data,
            lat='lat',
            lon='lon',
            hover_name='hover_text',
            color='role',
            color_discrete_map={'Hitter': '#00D4AA', 'Pitcher': '#FF6B6B'},
            zoom=3,
            height=500,  # Shorter map (was 700)
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

# ... (rest of your code — Recruitment Patterns, Players by Region, etc. remains unchanged)
