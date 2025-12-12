# Recruitment Patterns — Top States with % of total players
st.subheader("Recruitment Patterns (Top Recruiting States)")

if filtered.empty:
    st.write("No data matches current filters.")
else:
    # Only count — super lightweight
    state_counts = filtered['state'].value_counts().head(15).reset_index()
    state_counts.columns = ['state', 'count']
    state_counts['pct'] = (state_counts['count'] / len(filtered) * 100).round(1)
    state_counts = state_counts.sort_values('count')

    fig = px.bar(
        state_counts,
        x='count',
        y='state',
        orientation='h',
        text=state_counts['pct'].astype(str) + '%',
        height=600,
        color_discrete_sequence=['#E91E63']
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117',
        font_color='white',
        xaxis_title="Number of Players",
        yaxis_title="State"
    )
    st.plotly_chart(fig, use_container_width=True)
