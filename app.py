# ... (all the previous code for load_data, filters, table, maps, charts remains the same) ...

# AI Assistant (fixed to avoid crashes)
st.sidebar.header("AI Assistant (powered by Grok)")

if "grok_api_key" not in st.session_state:
    api_key = st.sidebar.text_input("Enter your Grok API key (from console.x.ai)", type="password")
    if api_key:
        st.session_state.grok_api_key = api_key
        st.sidebar.success("API key saved for this session!")
else:
    st.sidebar.success("API key loaded")
    api_key = st.session_state.grok_api_key

if "ai_chat" not in st.session_state:
    st.session_state.ai_chat = []

if api_key:
    user_question = st.sidebar.text_input("Ask about the current filtered data", key="ai_question")
    if st.sidebar.button("Send"):
        if user_question:
            with st.sidebar:
                with st.spinner("Asking Grok..."):
                    # FIXED: Much smaller summary to avoid crashes
                    data_summary = f"""
                    Current filtered data: {len(filtered)} players.
                    Available columns: {', '.join(filtered.columns.tolist())}
                    Role breakdown: {filtered['role'].value_counts().to_dict()}
                    Year range: {filtered['year'].min()} - {filtered['year'].max()}
                    Sample player names: {', '.join(filtered[['firstname', 'lastname']].head(3).apply(lambda x: f"{x['firstname']} {x['lastname']}", axis=1).tolist())}
                    Question: {user_question}
                    Please answer concisely using the data above. Use tables if helpful.
                    """
                    url = "https://api.x.ai/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {
                        "model": "grok-beta",
                        "messages": [{"role": "user", "content": data_summary}],
                        "temperature": 0.5
                    }
                    try:
                        response = requests.post(url, headers=headers, json=payload, timeout=30)
                        if response.status_code == 200:
                            answer = response.json()['choices'][0]['message']['content']
                        else:
                            answer = f"API error: {response.status_code} - {response.text}"
                    except Exception as e:
                        answer = f"Request error: {str(e)}"
                    st.session_state.ai_chat.append({"q": user_question, "a": answer})
                    st.rerun()

if st.session_state.ai_chat:
    st.sidebar.subheader("Chat History")
    for chat in st.session_state.ai_chat[-10:]:
        with st.sidebar.expander(chat["q"][:60] + ("..." if len(chat["q"]) > 60 else "")):
            st.write(chat["a"])
