# Recruitment patterns — now with % labels on top of each bar
st.subheader("Recruitment Patterns (Top States per Team)")
if not filtered.empty:
    top_states = filtered.groupby(['teamName', 'state']).size().reset_index(name='count')
    top_states = top_states.sort_values('count', ascending=False).head(20)
    
    # Calculate % of total players from each state
    total_players = len(filtered)
    top_states['percentage'] = (top_states['count'] / total_players * 100).round(1)
    
    fig_bar = px.bar(
        top_states,
        x='state',
        y='count',
        color='teamName',
        title='Top Recruiting States',
        text=top_states['percentage'].astype(str) + '%',  # <-- This adds the % on top
        hover_data={'count': True, 'percentage': ':.1f'}
    )
    
    # Put the % label on top of each bar
    fig_bar.update_traces(textposition='outside')
    
    # Clean look
    fig_bar.update_layout(
        uniformtext_minsize=9,
        uniformtext_mode='hide',
        xaxis_title="State",
        yaxis_title="Number of Players",
        legend_title="Team",
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117',
        font_color='white'
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.write("No data matches filters.")
