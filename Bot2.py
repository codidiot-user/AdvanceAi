import streamlit as st
import google.generativeai as genai
import requests
import json
from google.api_core import exceptions # +++ This is the new import line +++

# --- Page Configuration ---
st.set_page_config(
    page_title="QuantWeb AI",
    page_icon="🤖",
    layout="centered"
)

# --- API Configuration ---
try:
    # Configure the API keys securely using Streamlit Secrets
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    SERPER_API_KEY = st.secrets["SERPER_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("ERROR: API keys not found. Please add GOOGLE_API_KEY and SERPER_API_KEY to your .streamlit/secrets.toml file.")
    st.stop()


# --- System Prompt: The AI's "Brain" ---
SYSTEM_PROMPT = """
You are "Coditiot," a professional AI assistant created by Logesh S. 
You are an expert in electronics and Machine Learning.
Your tone should be helpful, knowledgeable, and concise. 
Provide clear, well-structured answers to assist the user.


Your capabilities include:
1.  **Answering Questions:** Provide clear, accurate, and well-structured answers on technology topics.
2.  **Code Analysis & Debugging:** When a user provides code with an error, you must:
    - Identify the error in the user's code.
    - Explain the cause of the error in simple terms.
    - Provide the complete, corrected code block.
    - Explain what you changed and why.
3.  **Web Search:** If a user's question requires real-time information (like news, recent events, or current data), you must use the provided search results to formulate your answer. Start your answer by saying "Searching the web, I found that..."

When using search results, synthesize the information into a comprehensive answer. Do not just list the search snippets.
"""

# --- Helper Functions ---

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
    """Orchestrates the AI response, deciding whether to search the web."""
    model = genai.GenerativeModel('gemini-1.5-flash')

    # First, ask a simple model if a web search is necessary
    search_checker_prompt = f"Does the following user query require a real-time web search to answer accurately? Query: '{user_prompt}'. Respond with only 'YES' or 'NO'."
    search_decision_model = genai.GenerativeModel('gemini-1.5-flash')
    search_decision = search_decision_model.generate_content(search_checker_prompt).text.strip().upper()

    final_prompt_for_history = user_prompt
    searched_web = False

    if "YES" in search_decision:
        searched_web = True
        st.write("Performing a real-time web search...")
        search_results = perform_web_search(user_prompt)

        # Create a new prompt that includes the search results for the main model
        final_prompt_for_history = f"""
        Based on the following web search results, please provide a comprehensive answer to the user's original query.

        **Search Results:**
        {json.dumps(search_results, indent=2)}

        **User's Original Query:**
        {user_prompt}
        """

    # Add the final prompt (either original or augmented with search results) to the history
    full_history = history + [{"role": "user", "parts": [final_prompt_for_history]}]

    generation_config = {
        "temperature": 0.7,
        "max_output_tokens": 2048,
    }

    response = model.generate_content(full_history, generation_config=generation_config)
    return response.text, searched_web

# --- Streamlit App UI ---

st.title("Codidiot AI Master")
st.markdown("Developed by Logesh")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "user", "parts": [SYSTEM_PROMPT]},
        {"role": "model", "parts": ["Understood. I am Gamkers, your expert AI assistant with live web access. How can I help you today?"]}
    ]

# Display past messages, skipping the initial system prompt
for message in st.session_state.messages[2:]:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"][0])

# Get user input
user_prompt = st.chat_input("Ask about coding, recent events, or anything else...")

if user_prompt:
    # Add user's message to history and display it
    st.session_state.messages.append({"role": "user", "parts": [user_prompt]})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Generate and display bot's response
    with st.chat_message("model"):
        with st.spinner("Getting Better results..."):
            try:
                # Get the AI response, which now returns both the text and whether a search was performed
                response_data, searched_web = get_ai_response(st.session_state.messages, user_prompt)

                # Show an indicator if a web search was used
                if searched_web:
                    st.info("I've used real-time web search to answer your question.", icon="💡")

                st.markdown(response_data)

                # Add the successful response to history
                st.session_state.messages.append({"role": "model", "parts": [response_data]})

            # +++ This is the updated error handling block +++
            except exceptions.ResourceExhausted as e:
                error_message = "I'm receiving too many requests right now. Please wait a moment before sending another message."
                st.error(error_message)

            except Exception as e:
                error_message = f"An unexpected error occurred. Please try again. Details: {e}"
                st.error(error_message)





