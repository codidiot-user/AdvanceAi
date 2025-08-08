import streamlit as st
import google.generativeai as genai
import requests
import json
from google.api_core import exceptions

# --- Page Configuration ---
st.set_page_config(
    page_title="Gamkers AI",
    page_icon="🤖",
    layout="centered"
)

# --- API Configuration ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    SERPER_API_KEY = st.secrets["SERPER_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("ERROR: API keys not found. Please add GOOGLE_API_KEY and SERPER_API_KEY to your .streamlit/secrets.toml file.")
    st.stop()


# --- System Prompt: The AI's "Brain" ---
SYSTEM_PROMPT = """
You are "Gamkers," a professional AI assistant created by Akash M. Your persona is that of an expert ethical hacker, cloud data engineer, and an experienced Python programmer. When using search results, synthesize the information into a comprehensive answer and start by saying "Searching the web, I found that...". For all other queries, respond directly.
"""

# --- Helper Functions ---

def is_search_query(prompt: str) -> bool:
    """
    Uses keywords to quickly determine if a prompt likely requires a web search.
    This avoids an extra API call.
    """
    prompt_lower = prompt.lower()
    # Keywords that strongly suggest a need for real-time information
    search_keywords = [
        "latest news", "current price", "who is", "what is the status of",
        "recent events", "today's weather", "what happened in", "summarize the news about"
    ]
    # Check if the prompt starts with a common question format needing current data
    if prompt_lower.startswith(("what is", "what are", "who is")):
        # Exclude simple conversational questions
        if "your name" not in prompt_lower and "your purpose" not in prompt_lower:
            return True
    # Check for any of the specific keywords
    for keyword in search_keywords:
        if keyword in prompt_lower:
            return True
    return False

def perform_web_search(query: str):
    """Performs a web search using the Serper API and returns results."""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"An error occurred during web search: {e}"

def get_ai_response(history, user_prompt):
    """Orchestrates the AI response, now with efficient keyword-based search decision."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    final_prompt_for_history = user_prompt
    searched_web = False

    # Use our new, fast function to decide if a search is needed
    if is_search_query(user_prompt):
        searched_web = True
        st.write("Performing a real-time web search...")
        search_results = perform_web_search(user_prompt)
        final_prompt_for_history = f"Based on these web search results: {json.dumps(search_results)}, provide a comprehensive answer to the user's original query: {user_prompt}"

    full_history = history + [{"role": "user", "parts": [final_prompt_for_history]}]

    generation_config = {"temperature": 0.7, "max_output_tokens": 2048}
    response = model.generate_content(full_history, generation_config=generation_config)
    return response.text, searched_web

# --- Streamlit App UI ---
st.title("Gamkers AI Assistant 🌐")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "user", "parts": [SYSTEM_PROMPT]},
        {"role": "model", "parts": ["Understood. I am Gamkers, your expert AI assistant with live web access. How can I help you today?"]}
    ]

for message in st.session_state.messages[2:]:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"][0])

user_prompt = st.chat_input("Ask about coding, recent events, or anything else...")

if user_prompt:
    st.session_state.messages.append({"role": "user", "parts": [user_prompt]})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("model"):
        with st.spinner("Gamkers is thinking..."):
            try:
                response_data, searched_web = get_ai_response(st.session_state.messages, user_prompt)
                if searched_web:
                    st.info("I've used real-time web search to answer your question.", icon="💡")
                st.markdown(response_data)
                st.session_state.messages.append({"role": "model", "parts": [response_data]})
            except exceptions.ResourceExhausted as e:
                st.error("I'm receiving too many requests right now. Please wait a moment and try again.")
            except Exception as e:
                st.error(f"An unexpected error occurred. Please try again. Details: {e}")
