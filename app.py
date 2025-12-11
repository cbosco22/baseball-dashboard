import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import numpy as np  # Needed for T90_per_PA

st.title("College Baseball Player Dashboard")

# Reset button at the top
if st.button("Reset All Filters"):
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

    # T90s and T90/PA
    df['Singles'] = df['H'] - df['Dbl'] - df['Tpl'] - df['HR']
    df['Singles'] = df['Singles'].fillna(0)
    df['TotalBases'] = df['Singles'] + 2*df['Dbl'].fillna(0) + 3*df['Tpl'].fillna(0) + 4*df['HR'].fillna(0)
    df['T90s'] = df['TotalBases'] + df['SB'].fillna(0) + df['BB'].fillna(0) + df['HBP'].fillna(0)
    df['PA'] = df['AB'].fillna(0) + df['BB'].fillna(0) + df['HBP'].fillna(0) + df['SF'].fillna(0) + df['SH'].fillna(0)
    df['T90_per_PA'] = df['T90s'] / df['PA'].replace(0, np.nan)
    df['T90_per_PA'] = df['T90_per_PA'].fillna(0)

    return df

data = load_data()

# --- Filters (same as before) ---
# (Copy all sidebar filters, base filtering, custom stat filters, draft, etc. from the last working version)
# ... paste them here ...

# --- Main content (table, maps, charts) ---
# (Copy from last working version)
# ... paste here ...

# --- AI Assistant ---
st.sidebar.header("AI Assistant (powered by Grok)")

if "grok_api_key" not in st.session_state:
    api_key = st.sidebar.text_input("Enter your Grok API key (from console.x.ai)", type="password")
    if api_key:
        st.session_state.grok_api_key = api_key
        st.sidebar.success("API key saved!")
else:
    st.sidebar.success("API key loaded")
    api_key = st.session_state.grok_api_key

if "ai_chat" not in st.session_state:
    st.session_state.ai_chat = []

if api_key:
    user_question = st.sidebar.text_input("Ask about the current filtered data")
    if st.sidebar.button("Send"):
        if user_question:
            with st.sidebar:
                with st.spinner("Asking Grok..."):
                    data_summary = f"Filtered data has {len(filtered)} players. Columns: {', '.join(filtered.columns)}. Sample:\n{filtered.head(3).to_string()}\nQuestion: {user_question}"
                    url = "https://api.x.ai/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {
                        "model": "grok-beta",
                        "messages": [{"role": "user", "content": data_summary}],
                        "temperature": 0.5
                    }
                    response = requests.post(url, headers=headers, json=payload)
                    if response.status_code == 200:
                        answer = response.json()['choices'][0]['message']['content']
                    else:
                        answer = f"API error: {response.text}"
                    st.session_state.ai_chat.append({"q": user_question, "a": answer})

if st.session_state.ai_chat:
    st.sidebar.subheader("Chat History")
    for chat in st.session_state.ai_chat[-5:]:
        with st.sidebar.expander(chat["q"][:50] + "..."):
            st.write(chat["a"])
