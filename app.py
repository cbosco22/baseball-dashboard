import streamlit as st
import pandas as pd
import plotly.express as px
import requests  # For API call
import json

st.title("College Baseball Player Dashboard")

# --- Load Data (same as before) ---
@st.cache_data
def load_data():
    # (Your full load_data function from previous version - copy it here exactly, including T90s calculation)
    # ... paste the entire load_data() from the last working version ...
    return df

data = load_data()

# --- All Filters (same as last version) ---
# (Copy all the sidebar filters, base filtering, custom stat filters, draft, etc. from the last working code)
# ... paste them here ...

# --- Main Content (player table, maps, charts) ---
# (Copy the player table, state map, recruitment, region/team graphs from last version)
# ... paste here ...

# --- AI Assistant Feature ---
st.sidebar.header("AI Assistant (powered by Grok)")

# API Key input (hidden after first entry)
if "grok_api_key" not in st.session_state:
    api_key = st.sidebar.text_input("Enter your Grok API key (from console.x.ai)", type="password")
    if api_key:
        st.session_state.grok_api_key = api_key
        st.sidebar.success("API key saved for this session!")
else:
    st.sidebar.success("API key loaded")
    api_key = st.session_state.grok_api_key

# Chat history
if "ai_chat" not in st.session_state:
    st.session_state.ai_chat = []

# User question input
if api_key:
    user_question = st.sidebar.text_input("Ask a question about the current filtered data (e.g., 'How many players from PA have over 20 HR?')")
    if st.sidebar.button("Send to AI Assistant"):
        if user_question:
            with st.sidebar:
                with st.spinner("Thinking..."):
                    # Prepare data summary for context
                    data_summary = f"""
                    Current filtered data has {len(filtered)} rows.
                    Columns: {', '.join(filtered.columns.tolist())}
                    Sample rows:
                    {filtered.head(5).to_string()}
                    Question: {user_question}
                    Please analyze and answer concisely, with tables if useful.
                    """
                    # Call Grok API
                    url = "https://api.x.ai/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": "grok-beta",
                        "messages": [{"role": "user", "content": data_summary}],
                        "temperature": 0.5
                    }
                    response = requests.post(url, headers=headers, json=payload)
                    if response.status_code == 200:
                        answer = response.json()['choices'][0]['message']['content']
                    else:
                        answer = f"Error: {response.status_code} - {response.text}"
                    
                    # Save to chat
                    st.session_state.ai_chat.append({"question": user_question, "answer": answer})
else:
    st.sidebar.info("Enter your Grok API key above to enable the AI Assistant.")

# Display chat history
if st.session_state.ai_chat:
    st.sidebar.subheader("AI Chat History")
    for chat in st.session_state.ai_chat[-10:]:  # Last 10 for space
        with st.sidebar.expander(chat["question"]):
            st.write(chat["answer"])
