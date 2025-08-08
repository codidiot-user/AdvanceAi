import streamlit as st
import google.generativeai as genai
import requests
import json

# Configure the API keys securely using Streamlit Secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
SERPER_API_KEY = st.secrets["SERPER_API_KEY"]

# --- This is the new, powerful system prompt that acts as the AI's "brain" ---
SYSTEM_PROMPT = """
You are "Gamkers," a professional AI assistant created by Akash M. 
Your persona is that of an expert ethical hacker, cloud data engineer, and an experienced Python programmer.

Your capabilities include:
1.  **Answering Questions:** Provide clear, accurate, and well-structured answers on technology topics.
2.  **Code Analysis & Debugging:** When a user provides code with an error, you must identify the error, explain it, and provide the corrected code.
3.  **Web Search:** If a user's question requires real-time information (like news, recent events, or current data), you must use the provided search results to formulate your answer. Start your answer by saying "Searching the web, I found that..."

When using search results, synthesize the information into a comprehensive answer. Do not just list the search snippets.
"""

# --- NEW Function to perform a web search ---
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

# --- UPDATED AI function to handle web search results ---
def get_ai_response(history, user_prompt):
    """Orchestrates the AI response, deciding whether to search the web."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # First, ask a simple model if a web search is necessary
    search_checker_prompt = f"Does the following user query require a real-time web search to answer accurately? Query: '{user_prompt}'. Respond with only 'YES' or 'NO'."
    search_decision_model = genai.GenerativeModel('gemini-1.5-flash')
    search_decision = search_decision_model.generate_content(search_checker_prompt).text.strip().upper()

    final_prompt = user_prompt

    if "YES" in search_decision:
        st.write("Performing a real-time web search...")
        search_results = perform_web_search(user_prompt)
        
        # Create a new prompt that includes the search results for the main model
        final_prompt = f"""
        Based on the following web search results, please provide a comprehensive answer to the user's original query.

        **Search Results:**
        {json.dumps(search_results, indent=2)}

        **User's Original Query:**
        {user_prompt}
        """

    # Add the final prompt (either original or augmented with search results) to the history
    full_history = history + [{"role": "user", "parts": [final_prompt]}]

    generation_config = {
        "temperature": 0.7,
        "max_output_tokens": 2048,
    }

    response = model.generate_content(full_history, generation_config=generation_config)
    return response.text, "YES" in search_decision

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
            response_data, searched_web = get_ai_response(st.session_state.messages, user_prompt)
            if searched_web:
                st.info("I've used real-time web search to answer your question.", icon="💡")
            st.markdown(response_data)
    
    st.session_state.messages.append({"role": "model", "parts": [response_data]})